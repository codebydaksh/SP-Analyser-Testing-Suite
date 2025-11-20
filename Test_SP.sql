USE [EDI]
GO

/****** Object:  StoredProcedure [dbo].[usp_Get_Google_Data_Export]    Script Date: 11/20/2025 2:57:37 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

 
 
-- ============================================
-- Google Customer Match Marketing Exclusion List - FINAL PRODUCTION VERSION
-- EMPLOYEES: Include NOT termed OR termed within last 365 days
-- CLIENTS: Include NOT termed OR termed within last 365 days  
-- NON-EMPLOYEES: Include once per unique EMAIL only (pick best record)
-- Output: SHA-256 hashed fields + plaintext Country/Zip (Production Mode)
--         OR Unhashed fields for QA validation (QA Mode)
-- FIX: Phone now includes + sign before hashing per Google requirements
-- FIX: Sanitize delimiter characters to prevent CSV column shift
-- FIX: ALL VARCHAR -> NVARCHAR (including Zip definition and Phone QA mode)
-- ============================================
CREATE   PROCEDURE [dbo].[usp_Get_Google_Data_Export]
    @IsProductionMode BIT = 1  -- 1 = Production (hashed), 0 = QA (unhashed)
AS
BEGIN
    SET NOCOUNT ON;
 
    -- Drop output table if exists
    IF OBJECT_ID('dbo.GoogleCustomerMatch_Output', 'U') IS NOT NULL
        DROP TABLE dbo.GoogleCustomerMatch_Output;
 
    WITH CombinedUsers AS (
        -- ============================================
        -- EMPLOYEE DATA
        -- Criteria: Non-termed employees + termed within last 365 days
        -- ============================================
        SELECT
            e.PersonId,
            COALESCE(
                NULLIF(LTRIM(RTRIM(e.WorkEmail)), ''), 
                NULLIF(LTRIM(RTRIM(p.HomeEmail)), '')
            ) AS RawEmail,
            pp.PhoneNumber AS RawPhone,
            p.FirstName AS RawFirstName,
            p.LastName AS RawLastName,
            a.ZipCode AS Zip,
            -- Prioritize home phone and mailing address
            ROW_NUMBER() OVER (
                PARTITION BY e.PersonId 
                ORDER BY 
                    CASE WHEN pp.PhoneTypeCode = 'H' THEN 0 ELSE 1 END,
                    CASE WHEN pa.AddressTypeCode = 'M' THEN 0 ELSE 1 END
            ) AS RowNum
        FROM dm1sql.portalselfservice.dbo.Client c
        INNER JOIN dm1sql.portaldirectory.dbo.ClientSetting cs 
            ON cs.clientno = c.ClientNumber
        INNER JOIN dm1sql.portalselfservice.dbo.Employee e 
            ON c.ClientId = e.ClientId
        INNER JOIN dm1sql.portalselfservice.dbo.Person p 
            ON e.PersonId = p.PersonId
        LEFT JOIN dm1sql.portalselfservice.dbo.PersonAddress pa 
            ON p.PersonId = pa.PersonId
        LEFT JOIN dm1sql.portalselfservice.dbo.Address a 
            ON pa.AddressId = a.AddressId
        LEFT JOIN dm1sql.portalselfservice.dbo.PersonPhone pp 
            ON p.PersonId = pp.PersonId
        WHERE 
            -- Employee: NOT termed OR termed within 365 days
            (e.PEOTerminationDate IS NULL OR e.PEOTerminationDate >= CAST(DATEADD(DAY, -365, GETDATE()) AS DATE))
            -- Client: NOT termed OR termed within 365 days
            AND (c.PEOTerminationDate IS NULL OR c.PEOTerminationDate >= CAST(DATEADD(DAY, -365, GETDATE()) AS DATE))
            -- Exclude demo/test only (per client guidance)
            AND cs.isdemo = 0
            AND cs.istest = 0
 
        UNION ALL
 
        -- ============================================
        -- NON-EMPLOYEE DATA
        -- Keep ALL valid client associations initially
        -- Will deduplicate by email after cleaning
        -- ============================================
        SELECT
            ne.Id AS PersonId,
            ne.EmailAddress AS RawEmail,
            ne.HomePhoneNumber AS RawPhone,
            ne.FirstName AS RawFirstName,
            ne.LastName AS RawLastName,
            ne.ZipCode AS Zip,
            1 AS RowNum  -- Keep all initially
        FROM dm1sql.portaldirectory.dbo.NonEmployee ne
        INNER JOIN dm1sql.portaldirectory.dbo.SecurityProfile sp 
            ON ne.Id = sp.EmployeeNo
        INNER JOIN dm1sql.portalselfservice.dbo.Client c 
            ON c.ClientNumber = sp.ClientNo
        INNER JOIN dm1sql.portaldirectory.dbo.ClientSetting cs 
            ON cs.clientno = c.ClientNumber
        WHERE 
            -- Client: NOT termed OR termed within 365 days
            (c.PEOTerminationDate IS NULL OR c.PEOTerminationDate >= CAST(DATEADD(DAY, -365, GETDATE()) AS DATE))
            -- Exclude demo/test only (per client guidance)
            AND cs.isdemo = 0
            AND cs.istest = 0
    ),
    -- ============================================
    -- STEP 1: Filter to RowNum = 1 for employees
    -- ============================================
    Filtered AS (
        SELECT
            RawEmail,
            RawPhone,
            RawFirstName,
            RawLastName,
            Zip
        FROM CombinedUsers
        WHERE RowNum = 1
    ),
    -- ============================================
    -- STEP 2: DATA CLEANING & VALIDATION
    -- All fields lowercase & trim whitespace
    -- FIXED: Phone now includes + sign per Google requirement
    -- FIXED: Zip now NVARCHAR instead of VARCHAR
    -- ============================================
    Cleaned AS (
        SELECT
            -- Email: Must contain @ and . with no spaces, then lowercase & trim
            CASE 
                WHEN RawEmail LIKE '%@%.%' AND CHARINDEX(' ', RawEmail) = 0 
                THEN LOWER(LTRIM(RTRIM(RawEmail))) 
                ELSE NULL 
            END AS CleanEmail,
            -- Phone: Format to E.164 US format (+1XXXXXXXXXX) - ENSURE + SIGN IS INCLUDED
            CASE 
                WHEN dbo.fn_FormatPhoneToE164_US(RawPhone) IS NOT NULL THEN
                    -- Check if + sign is already present
                    CASE 
                        WHEN LEFT(dbo.fn_FormatPhoneToE164_US(RawPhone), 1) = '+' 
                        THEN dbo.fn_FormatPhoneToE164_US(RawPhone)
                        -- If + missing, add it
                        ELSE '+' + dbo.fn_FormatPhoneToE164_US(RawPhone)
                    END
                ELSE NULL
            END AS CleanPhone,
            -- Names: Remove prefixes, lowercase, trim
            dbo.fn_CleanName(RawFirstName) AS CleanFirstName,
            dbo.fn_CleanName(RawLastName) AS CleanLastName,
            -- Zip: Trim only (must remain plaintext) - FIXED: Changed to NVARCHAR
            CAST(LTRIM(RTRIM(Zip)) AS NVARCHAR(10)) AS Zip
        FROM Filtered
        WHERE RawEmail IS NOT NULL  -- Must have email
    ),
    -- ============================================
    -- STEP 2.5: SANITIZE CSV DELIMITER CHARACTERS
    -- Remove commas, tabs, newlines, carriage returns, and quotes
    -- This prevents CSV column shift issues during export
    -- ============================================
    Sanitized AS (
        SELECT
            CleanEmail,
            -- Remove delimiter characters from all fields
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(CleanPhone, ',', ''), CHAR(9), ''), CHAR(10), ''), CHAR(13), ''), '"', '') AS CleanPhone,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(CleanFirstName, ',', ''), CHAR(9), ''), CHAR(10), ''), CHAR(13), ''), '"', '') AS CleanFirstName,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(CleanLastName, ',', ''), CHAR(9), ''), CHAR(10), ''), CHAR(13), ''), '"', '') AS CleanLastName,
            REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(Zip, ',', ''), CHAR(9), ''), CHAR(10), ''), CHAR(13), ''), '"', '') AS Zip
        FROM Cleaned
        WHERE CleanEmail IS NOT NULL
    ),
    -- ============================================
    -- STEP 3: Deduplicate by EMAIL ONLY
    -- Pick ONE record per email (prioritize: phone not null, then alphabetically)
    -- ============================================
    EmailDeduped AS (
        SELECT
            CleanEmail,
            CleanPhone,
            CleanFirstName,
            CleanLastName,
            Zip,
            ROW_NUMBER() OVER (
                PARTITION BY CleanEmail 
                ORDER BY 
                    CASE WHEN CleanPhone IS NOT NULL THEN 0 ELSE 1 END,
                    CleanFirstName,
                    CleanLastName,
                    Zip
            ) AS EmailRowNum
        FROM Sanitized  -- Changed from Cleaned to Sanitized
        WHERE CleanEmail IS NOT NULL  -- CRITICAL: Ensure email is not NULL after cleaning
    )
    -- ============================================
    -- CREATE OUTPUT TABLE WITH CONDITIONAL HASHING
    -- Production Mode (@IsProductionMode = 1): SHA-256 hashed fields
    -- QA Mode (@IsProductionMode = 0): Unhashed fields for validation
    -- FIXED: Phone includes + sign before hashing
    -- FIXED: All fields sanitized to prevent CSV column shift
    -- FIXED: ALL output fields explicitly NVARCHAR (including Phone QA mode)
    -- ============================================
    SELECT
        -- Email: Hashed in production, unhashed in QA mode
        CASE 
            WHEN @IsProductionMode = 1 THEN CONVERT(NVARCHAR(255), HASHBYTES('SHA2_256', CleanEmail), 2)
            ELSE CONVERT(NVARCHAR(255), CleanEmail)
        END AS Email,

        -- First Name: Hashed in production, unhashed in QA mode
        CASE 
            WHEN @IsProductionMode = 1 THEN CONVERT(NVARCHAR(255), HASHBYTES('SHA2_256', CleanFirstName), 2)
            ELSE CONVERT(NVARCHAR(255), CleanFirstName)
        END AS [First Name],

        -- Last Name: Hashed in production, unhashed in QA mode
        CASE 
            WHEN @IsProductionMode = 1 THEN CONVERT(NVARCHAR(255), HASHBYTES('SHA2_256', CleanLastName), 2)
            ELSE CONVERT(NVARCHAR(255), CleanLastName)
        END AS [Last Name],

        -- Country: Always plaintext
        CONVERT(NVARCHAR(10), 'US') AS Country,

        -- Zip: Always plaintext
        CONVERT(NVARCHAR(20), Zip) AS Zip,

        -- Phone: Hashed in production (with + sign), unhashed in QA mode
        -- CRITICAL: Phone now includes + sign before hashing per Google requirement
        -- FIXED: QA mode now explicitly converts to NVARCHAR
        CASE 
            WHEN @IsProductionMode = 1 THEN 
                CONVERT(NVARCHAR(255), HASHBYTES('SHA2_256', CleanPhone), 2)
            ELSE 
                -- Add apostrophe prefix for QA mode - forces Excel text format
                -- FIXED: Explicitly convert to NVARCHAR to prevent Unicode/Non-Unicode errors
                CONVERT(NVARCHAR(255),
                    CASE 
                        WHEN CleanPhone IS NOT NULL THEN '="' + CleanPhone + '"'
                        ELSE NULL
                    END
                )
        END AS Phone
    INTO dbo.GoogleCustomerMatch_Output
    FROM EmailDeduped
    WHERE EmailRowNum = 1
        AND CleanEmail IS NOT NULL;  -- ADDED: Double-check email is not NULL
 
    -- Return results in the specific order required by Google
    SELECT
        Email,
        [First Name],
        [Last Name],
        Country,
        Zip,
        Phone
    FROM dbo.GoogleCustomerMatch_Output;
 
END;
GO


