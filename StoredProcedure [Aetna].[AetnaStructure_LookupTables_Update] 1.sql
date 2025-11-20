-- Step 1: Create and populate the first temp table for Account Structure
DROP TABLE IF EXISTS #AccountStructureExtract
CREATE TABLE #AccountStructureExtract
(
    ControlNumber	varchar(50),
    Suffix			varchar(50),
    Network			varchar(50),
    Band			varchar(50),
    Account_Active	varchar(50),
    Account_COBRA	varchar(50),
    DepAge30Flag	varchar(2)
)
INSERT INTO #AccountStructureExtract(ControlNumber,Suffix,Network,Band,Account_Active,Account_COBRA,DepAge30Flag)
SELECT	ControlNumber	
        ,Right(Suffix,2) AS Suffix			
        ,Network			
        ,Band			
        ,Account_Active	
        ,Account_COBRA
        ,DepAge30Flag	
FROM [EDI].[Aetna].[AccountStructure_Accounts_Extract];
-- Show records after initial insert
SELECT 'After initial insert into #AccountStructureExtract' AS Step, COUNT(*) AS RecordCount
FROM #AccountStructureExtract
-- Show some sample records
SELECT TOP 10 * 
FROM #AccountStructureExtract

---Remove duplicates from Accounts_Extract staging table
-- First, let's create a temp table to store what we're going to delete
DROP TABLE IF EXISTS #AccountStructureDuplicates
CREATE TABLE #AccountStructureDuplicates
(
    ControlNumber	varchar(50),
    Suffix			varchar(50),
    Network			varchar(50),
    Band			varchar(50),
    Account_Active	varchar(50),
    Account_COBRA	varchar(50),
    DepAge30Flag	varchar(2),
    Rk				int
)
-- Insert the duplicates into our temp table
;WITH CTE_RemoveDups_AccountStructure  -- Added semicolon before CTE
AS
(
    SELECT 	[ControlNumber]
            ,RIGHT([Suffix],2) AS [Suffix]
            ,[Network]
            ,[Band]
            ,[Account_Active]
            ,[Account_COBRA]
            ,[DepAge30Flag]
          ,ROW_NUMBER() OVER (PARTITION BY [ControlNumber],[Suffix],[Network],[Account_Active],[Account_COBRA],[Band],[DepAge30Flag] 
          ORDER BY [ControlNumber],[Suffix],[Network],[Account_Active],[Account_COBRA],[Band],[DepAge30Flag]) AS Rk
    FROM [EDI].[Aetna].[AccountStructure_Accounts_Extract]
)
INSERT INTO #AccountStructureDuplicates
SELECT 	[ControlNumber]
        ,[Suffix]
        ,[Network]
        ,[Band]
        ,[Account_Active]
        ,[Account_COBRA]
        ,[DepAge30Flag]
        ,Rk
FROM CTE_RemoveDups_AccountStructure
WHERE Rk > 1
-- Show how many duplicates we found
SELECT 'Duplicates found in #AccountStructureExtract' AS Step, COUNT(*) AS RecordCount
FROM #AccountStructureDuplicates
-- Show some sample duplicates
SELECT TOP 10 * 
FROM #AccountStructureDuplicates
-- Now delete the duplicates
DELETE A
FROM #AccountStructureExtract A
INNER JOIN #AccountStructureDuplicates dups
    ON A.ControlNumber=dups.ControlNumber
    AND A.Suffix=dups.Suffix
    AND A.Network=dups.Network
    AND A.Band=dups.Band
    AND A.[Account_Active]=dups.[Account_Active]
    AND A.[Account_COBRA]=dups.[Account_COBRA]
    AND A.[DepAge30Flag]=dups.[DepAge30Flag]
-- Show records after removing duplicates
SELECT 'After removing duplicates from #AccountStructureExtract' AS Step, COUNT(*) AS RecordCount
FROM #AccountStructureExtract
-- Create a temp table for the lookup data to compare against
DROP TABLE IF EXISTS #TempLookupAccount
CREATE TABLE #TempLookupAccount
(
    ControlNumber	varchar(50),
    Suffix			varchar(50),
    Network			varchar(50),
    Band			varchar(50),
    Account_Active	varchar(50),
    Account_COBRA	varchar(50),
    DepAge30Flag	varchar(2)
)
-- Copy existing lookup data to temp table
INSERT INTO #TempLookupAccount
SELECT ControlNumber, Suffix, Network, Band, Account_Active, Account_COBRA, DepAge30Flag
FROM [Aetna].[lookup_AccountStructure_Account]
-- Show how many records are in the lookup table
SELECT 'Records in #TempLookupAccount (existing lookup data)' AS Step, COUNT(*) AS RecordCount
FROM #TempLookupAccount
-- Create a temp table to store what we would insert (but not actually inserting)
DROP TABLE IF EXISTS #NewAccountRecords
CREATE TABLE #NewAccountRecords
(
    ControlNumber	varchar(50),
    Suffix			varchar(50),
    Network			varchar(50),
    Band			varchar(50),
    Account_Active	varchar(50),
    Account_COBRA	varchar(50),
    DepAge30Flag	varchar(2)
)
-- Insert the new records into our temp table (not the main table)
INSERT INTO #NewAccountRecords
SELECT ase.ControlNumber,ase.Suffix,ase.Network,ase.Band,ase.Account_Active,ase.Account_COBRA,ase.DepAge30Flag
FROM #TempLookupAccount lasa
RIGHT OUTER JOIN #AccountStructureExtract ase
ON 
    lasa.ControlNumber=ase.ControlNumber
AND lasa.Suffix=ase.Suffix
AND lasa.Network=ase.Network
AND lasa.Band=ase.Band
AND lasa.DepAge30Flag=ase.DepAge30Flag
WHERE lasa.ControlNumber IS NULL
-- Show how many new records we found
SELECT 'New records that would be inserted into lookup_AccountStructure_Account' AS Step, COUNT(*) AS RecordCount
FROM #NewAccountRecords
-- Show some sample new records
SELECT TOP 10 * 
FROM #NewAccountRecords
-- We are NOT inserting into the main table as requested

-----PlanID Updates
-- Step 2: Create and populate the temp table for PlanID
DROP TABLE IF EXISTS #AccountStructurePlanIDExtract
CREATE TABLE #AccountStructurePlanIDExtract
(
    ControlNumber		varchar(50),
    Suffix				varchar(50),
    Network				varchar(50),
    [State]				varchar(50),
    [IsCoverageBased]	varchar(50),
    CoverageRules		varchar(50),
    PlanId				varchar(50),
    DepAge30Flag	    varchar(2)
)
INSERT INTO #AccountStructurePlanIDExtract(ControlNumber,Suffix,Network,[State],[IsCoverageBased],CoverageRules,PlanId,DepAge30Flag)
SELECT	ControlNumber	
        ,Right(Suffix,2) AS Suffix			
        ,Network			
        ,[State]			
        ,[IsCoverageBased]	
        ,CoverageRules
        ,PlanId
        ,DepAge30Flag	
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract];
-- Show records after initial insert
SELECT 'After initial insert into #AccountStructurePlanIDExtract' AS Step, COUNT(*) AS RecordCount
FROM #AccountStructurePlanIDExtract
-- Show some sample records
SELECT TOP 10 * 
FROM #AccountStructurePlanIDExtract

-- NEW: Check PlanId values in the extract table
SELECT 'PlanId values in extract table (initial)' AS Step, 
       PlanId, 
       COUNT(*) AS Count
FROM #AccountStructurePlanIDExtract
GROUP BY PlanId
ORDER BY PlanId

-- NEW: Check for string-based PlanIds in extract table
SELECT 'String-based PlanIds in extract table (initial)' AS Step, 
       PlanId, 
       COUNT(*) AS Count
FROM #AccountStructurePlanIDExtract
WHERE PlanId LIKE '%[^0-9]%' AND PlanId <> ''
GROUP BY PlanId
ORDER BY PlanId

---Remove duplicates from PlanID_Extract staging table
-- First, let's create a temp table to store what we're going to delete
DROP TABLE IF EXISTS #AccountStructurePlanIDDuplicates
CREATE TABLE #AccountStructurePlanIDDuplicates
(
    ControlNumber		varchar(50),
    Suffix				varchar(50),
    Network				varchar(50),
    [State]				varchar(50),
    [IsCoverageBased]	varchar(50),
    CoverageRules		varchar(50),
    PlanId				varchar(50),
    DepAge30Flag	    varchar(2),
    Rk					int
)
-- Insert the duplicates into our temp table
;WITH CTE_RemoveDups_PlanID  -- Added semicolon before CTE
AS
(
    SELECT 	[ControlNumber]
            ,RIGHT([Suffix],2) AS [Suffix]
            ,[Network]
            ,[State]
            ,[IsCoverageBased]
            ,[CoverageRules]
            ,[PlanID]
            ,[DepAge30Flag]
          ,ROW_NUMBER() OVER (PARTITION BY [ControlNumber],[Suffix],[Network],[State],[DepAge30Flag] ORDER BY [ControlNumber],[Suffix],[Network],[State],[DepAge30Flag]) AS Rk
    FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract]
)
INSERT INTO #AccountStructurePlanIDDuplicates
SELECT 	[ControlNumber]
        ,[Suffix]
        ,[Network]
        ,[State]
        ,[IsCoverageBased]
        ,[CoverageRules]
        ,[PlanID]
        ,[DepAge30Flag]
        ,Rk
FROM CTE_RemoveDups_PlanID
WHERE Rk > 1
-- Show how many duplicates we found
SELECT 'Duplicates found in #AccountStructurePlanIDExtract' AS Step, COUNT(*) AS RecordCount
FROM #AccountStructurePlanIDDuplicates
-- Show some sample duplicates
SELECT TOP 10 * 
FROM #AccountStructurePlanIDDuplicates

-- NEW: Check PlanId values in the duplicates table
SELECT 'PlanId values in duplicates table' AS Step, 
       PlanId, 
       COUNT(*) AS Count
FROM #AccountStructurePlanIDDuplicates
GROUP BY PlanId
ORDER BY PlanId

-- Now delete the duplicates
DELETE A
FROM #AccountStructurePlanIDExtract A
INNER JOIN #AccountStructurePlanIDDuplicates dups
    ON A.ControlNumber=dups.ControlNumber
    AND A.Suffix=dups.Suffix
    AND A.Network=dups.Network
    AND A.[State]=dups.[State]
    AND A.[DepAge30Flag]=dups.DepAge30Flag
-- Show records after removing duplicates
SELECT 'After removing duplicates from #AccountStructurePlanIDExtract' AS Step, COUNT(*) AS RecordCount
FROM #AccountStructurePlanIDExtract

-- NEW: Check PlanId values in the extract table after deduplication
SELECT 'PlanId values in extract table (after deduplication)' AS Step, 
       PlanId, 
       COUNT(*) AS Count
FROM #AccountStructurePlanIDExtract
GROUP BY PlanId
ORDER BY PlanId

-- Create a temp table for the lookup data to compare against
DROP TABLE IF EXISTS #TempLookupPlanID
CREATE TABLE #TempLookupPlanID
(
    ControlNumber		varchar(50),
    Suffix				varchar(50),
    Network				varchar(50),
    [State]				varchar(50),
    [IsCoverageBased]	varchar(50),
    CoverageRules		varchar(50),
    PlanId				varchar(50),
    DepAge30Flag	    varchar(2)
)
-- Copy existing lookup data to temp table
INSERT INTO #TempLookupPlanID
SELECT ControlNumber, Suffix, Network, [State], IsCoverageBased, CoverageRules, PlanId, DepAge30Flag
FROM EDI.[Aetna].[lookup_AccountStructure_PlanID]
-- Show how many records are in the lookup table
SELECT 'Records in #TempLookupPlanID (existing lookup data)' AS Step, COUNT(*) AS RecordCount
FROM #TempLookupPlanID

-- NEW: Check PlanId values in the lookup table
SELECT 'PlanId values in lookup table' AS Step, 
       PlanId, 
       COUNT(*) AS Count
FROM #TempLookupPlanID
GROUP BY PlanId
ORDER BY PlanId

-- NEW: Check for string-based PlanIds in lookup table
SELECT 'String-based PlanIds in lookup table' AS Step, 
       PlanId, 
       COUNT(*) AS Count
FROM #TempLookupPlanID
WHERE PlanId LIKE '%[^0-9]%' AND PlanId <> ''
GROUP BY PlanId
ORDER BY PlanId

-- Create a temp table to store what we would insert (but not actually inserting)
DROP TABLE IF EXISTS #NewPlanIDRecords
CREATE TABLE #NewPlanIDRecords
(
    ControlNumber		varchar(50),
    Suffix				varchar(50),
    Network				varchar(50),
    [State]				varchar(50),
    [IsCoverageBased]	varchar(50),
    CoverageRules		varchar(50),
    PlanId				varchar(50),
    DepAge30Flag	    varchar(2)
)
-- Insert the new records into our temp table (not the main table)
INSERT INTO #NewPlanIDRecords
SELECT ase.ControlNumber,ase.Suffix,ase.Network,ase.[State],ase.IsCoverageBased,ase.CoverageRules,ase.PlanId,ase.DepAge30Flag
FROM #TempLookupPlanID la
RIGHT OUTER JOIN #AccountStructurePlanIDExtract ase
ON 
    la.ControlNumber=ase.ControlNumber
AND la.Suffix=ase.Suffix
AND la.Network=ase.Network
AND la.[State]=ase.[State]
AND la.DepAge30Flag=ase.DepAge30Flag
WHERE la.ControlNumber IS NULL
-- Show how many new records we found
SELECT 'New records that would be inserted into lookup_AccountStructure_PlanID' AS Step, COUNT(*) AS RecordCount
FROM #NewPlanIDRecords
-- Show some sample new records
SELECT TOP 10 * 
FROM #NewPlanIDRecords

-- NEW: Check PlanId values in the new records table
SELECT 'PlanId values in new records table' AS Step, 
       PlanId, 
       COUNT(*) AS Count
FROM #NewPlanIDRecords
GROUP BY PlanId
ORDER BY PlanId

-- NEW: Compare PlanId values between lookup and extract tables
SELECT 
    'PlanId comparison between lookup and extract' AS Step,
    la.ControlNumber,
    la.Suffix,
    la.Network AS lookup_Network,
    la.[State] AS lookup_State,
    la.PlanId AS lookup_PlanId,
    ase.Network AS extract_Network,
    ase.[State] AS extract_State,
    ase.PlanId AS extract_PlanId,
    CASE 
        WHEN la.PlanId LIKE '%[^0-9]%' AND ase.PlanId NOT LIKE '%[^0-9]%' THEN 'String vs Numeric'
        WHEN la.PlanId NOT LIKE '%[^0-9]%' AND ase.PlanId LIKE '%[^0-9]%' THEN 'Numeric vs String'
        WHEN la.PlanId <> ase.PlanId THEN 'Different Values'
        ELSE 'Same Values'
    END AS Comparison_Result
FROM #TempLookupPlanID la
INNER JOIN #AccountStructurePlanIDExtract ase
    ON la.ControlNumber = ase.ControlNumber
    AND la.Suffix = ase.Suffix
    AND ISNULL(la.DepAge30Flag, 0) = ISNULL(ase.DepAge30Flag, 0)
WHERE la.PlanId <> ase.PlanId
ORDER BY la.ControlNumber, la.Suffix, la.[State]


-- NEW: Detailed analysis of the PlanId differences
-- Let's see the full context of the records that have different PlanIds
SELECT 
    'Detailed analysis of PlanId differences' AS Step,
    la.ControlNumber,
    la.Suffix,
    la.Network AS lookup_Network,
    la.[State] AS lookup_State,
    la.IsCoverageBased AS lookup_IsCoverageBased,
    la.CoverageRules AS lookup_CoverageRules,
    la.PlanId AS lookup_PlanId,
    la.DepAge30Flag AS lookup_DepAge30Flag,
    ase.Network AS extract_Network,
    ase.[State] AS extract_State,
    ase.IsCoverageBased AS extract_IsCoverageBased,
    ase.CoverageRules AS extract_CoverageRules,
    ase.PlanId AS extract_PlanId,
    ase.DepAge30Flag AS extract_DepAge30Flag
FROM #TempLookupPlanID la
INNER JOIN #AccountStructurePlanIDExtract ase
    ON la.ControlNumber = ase.ControlNumber
    AND la.Suffix = ase.Suffix
    AND ISNULL(la.DepAge30Flag, 0) = ISNULL(ase.DepAge30Flag, 0)
WHERE la.PlanId <> ase.PlanId
ORDER BY la.ControlNumber, la.Suffix, la.[State]

-- NEW: Check if the lookup table has multiple records for the same ControlNumber/Suffix
SELECT 
    'Multiple records per ControlNumber/Suffix in lookup table' AS Step,
    ControlNumber,
    Suffix,
    COUNT(*) AS RecordCount,
    STUFF((
        SELECT DISTINCT ', ' + [State]
        FROM #TempLookupPlanID t2
        WHERE t2.ControlNumber = t1.ControlNumber AND t2.Suffix = t1.Suffix
        FOR XML PATH('')
    ), 1, 2, '') AS States,
    STUFF((
        SELECT DISTINCT ', ' + PlanId
        FROM #TempLookupPlanID t2
        WHERE t2.ControlNumber = t1.ControlNumber AND t2.Suffix = t1.Suffix
        FOR XML PATH('')
    ), 1, 2, '') AS PlanIds
FROM #TempLookupPlanID t1
GROUP BY ControlNumber, Suffix
HAVING COUNT(*) > 1
ORDER BY ControlNumber, Suffix

-- NEW: Check if the extract table has multiple records for the same ControlNumber/Suffix
SELECT 
    'Multiple records per ControlNumber/Suffix in extract table' AS Step,
    ControlNumber,
    Suffix,
    COUNT(*) AS RecordCount,
    STUFF((
        SELECT DISTINCT ', ' + [State]
        FROM #AccountStructurePlanIDExtract t2
        WHERE t2.ControlNumber = t1.ControlNumber AND t2.Suffix = t1.Suffix
        FOR XML PATH('')
    ), 1, 2, '') AS States,
    STUFF((
        SELECT DISTINCT ', ' + PlanId
        FROM #AccountStructurePlanIDExtract t2
        WHERE t2.ControlNumber = t1.ControlNumber AND t2.Suffix = t1.Suffix
        FOR XML PATH('')
    ), 1, 2, '') AS PlanIds
FROM #AccountStructurePlanIDExtract t1
GROUP BY ControlNumber, Suffix
HAVING COUNT(*) > 1
ORDER BY ControlNumber, Suffix

-- NEW: Compare the structure of the two tables
SELECT 
    'Structure comparison between lookup and extract tables' AS Step,
    'Lookup table' AS TableType,
    ControlNumber,
    Suffix,
    COUNT(DISTINCT [State]) AS StateCount,
    COUNT(DISTINCT PlanId) AS PlanIdCount
FROM #TempLookupPlanID
GROUP BY ControlNumber, Suffix

UNION ALL

SELECT 
    'Structure comparison between lookup and extract tables' AS Step,
    'Extract table' AS TableType,
    ControlNumber,
    Suffix,
    COUNT(DISTINCT [State]) AS StateCount,
    COUNT(DISTINCT PlanId) AS PlanIdCount
FROM #AccountStructurePlanIDExtract
GROUP BY ControlNumber, Suffix
ORDER BY ControlNumber, Suffix, TableType






-- Add this section at the end of your stored procedure

-- NEW: Analysis of string-based PlanIds in lookup table
SELECT 
    'Analysis of string-based PlanIds in lookup table' AS Step,
    la.ControlNumber,
    la.Suffix,
    la.Network AS lookup_Network,
    la.[State] AS lookup_State,
    la.IsCoverageBased AS lookup_IsCoverageBased,
    la.CoverageRules AS lookup_CoverageRules,
    la.PlanId AS lookup_PlanId,
    la.DepAge30Flag AS lookup_DepAge30Flag,
    ase.Network AS extract_Network,
    ase.[State] AS extract_State,
    ase.IsCoverageBased AS extract_IsCoverageBased,
    ase.CoverageRules AS extract_CoverageRules,
    ase.PlanId AS extract_PlanId,
    ase.DepAge30Flag AS extract_DepAge30Flag
FROM #TempLookupPlanID la
LEFT JOIN #AccountStructurePlanIDExtract ase
    ON la.ControlNumber = ase.ControlNumber
    AND la.Suffix = ase.Suffix
    AND ISNULL(la.DepAge30Flag, 0) = ISNULL(ase.DepAge30Flag, 0)
WHERE la.PlanId LIKE '%[^0-9]%'  -- String-based PlanIds
ORDER BY la.ControlNumber, la.Suffix, la.[State]

-- NEW: Summary of PlanId patterns
SELECT 
    'Summary of PlanId patterns' AS Step,
    'Lookup table' AS TableType,
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END AS PlanIdPattern,
    COUNT(*) AS RecordCount
FROM #TempLookupPlanID
GROUP BY 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END

UNION ALL

SELECT 
    'Summary of PlanId patterns' AS Step,
    'Extract table' AS TableType,
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END AS PlanIdPattern,
    COUNT(*) AS RecordCount
FROM #AccountStructurePlanIDExtract
GROUP BY 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END
ORDER BY TableType, PlanIdPattern

-- We are NOT inserting into the main table as requested




-- Create a corrected version of the lookup table
DROP TABLE IF EXISTS #CorrectedLookupPlanID
CREATE TABLE #CorrectedLookupPlanID
(
    ControlNumber		varchar(50),
    Suffix				varchar(50),
    Network				varchar(50),
    [State]				varchar(50),
    [IsCoverageBased]	varchar(50),
    CoverageRules		varchar(50),
    PlanId				varchar(50),
    DepAge30Flag	    varchar(2),
    SourceTable			varchar(20)  -- To track where the record came from
)

-- Step 1: Insert all records from the extract table (this will be our base)
INSERT INTO #CorrectedLookupPlanID
SELECT 
    ControlNumber,
    Suffix,
    Network,
    [State],
    IsCoverageBased,
    CoverageRules,
    PlanId,
    DepAge30Flag,
    'Extract' AS SourceTable
FROM #AccountStructurePlanIDExtract

-- Step 2: For records in the lookup table that don't exist in the extract table, add them
-- But convert string-based PlanIds to numeric if possible
INSERT INTO #CorrectedLookupPlanID
SELECT 
    la.ControlNumber,
    la.Suffix,
    la.Network,
    la.[State],
    la.IsCoverageBased,
    la.CoverageRules,
    -- Convert string-based PlanIds to a default numeric PlanId based on Suffix
    CASE 
        WHEN la.PlanId LIKE '%[^0-9]%' THEN 
            CASE la.Suffix
                WHEN '10' THEN '00100'
                WHEN '11' THEN '10100'
                WHEN '12' THEN '20100'
                WHEN '14' THEN '40100'
                WHEN '15' THEN '50100'
                ELSE '00000'
            END
        ELSE la.PlanId
    END AS PlanId,
    la.DepAge30Flag,
    'Lookup' AS SourceTable
FROM #TempLookupPlanID la
LEFT JOIN #AccountStructurePlanIDExtract ase
    ON la.ControlNumber = ase.ControlNumber
    AND la.Suffix = ase.Suffix
    AND la.[State] = ase.[State]
WHERE ase.ControlNumber IS NULL

-- Step 3: Handle the string-based PlanIds that don't have a matching State in the extract table
-- We'll create a mapping for these
INSERT INTO #CorrectedLookupPlanID
SELECT 
    la.ControlNumber,
    la.Suffix,
    la.Network,
    la.[State],
    la.IsCoverageBased,
    la.CoverageRules,
    -- Map string-based PlanIds to numeric ones
    CASE la.PlanId
        WHEN 'CMAPOS10' THEN '00100'
        WHEN 'CMAPOS11' THEN '10100'
        WHEN 'CMAPOS12' THEN '20100'
        WHEN 'CMAPOS13' THEN '30100'
        WHEN 'CMAPOS14' THEN '40100'
        WHEN 'CMAPOS15' THEN '50100'
        ELSE la.PlanId
    END AS PlanId,
    la.DepAge30Flag,
    'Lookup_Converted' AS SourceTable
FROM #TempLookupPlanID la
WHERE la.PlanId LIKE '%[^0-9]%'  -- String-based PlanIds
AND NOT EXISTS (
    SELECT 1 FROM #CorrectedLookupPlanID c
    WHERE c.ControlNumber = la.ControlNumber
    AND c.Suffix = la.Suffix
    AND c.[State] = la.[State]
)

-- Now let's see the results
SELECT 'Corrected lookup table record count' AS Step, COUNT(*) AS RecordCount
FROM #CorrectedLookupPlanID

-- Show PlanId patterns in the corrected table
SELECT 
    'PlanId patterns in corrected lookup table' AS Step,
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END AS PlanIdPattern,
    COUNT(*) AS RecordCount
FROM #CorrectedLookupPlanID
GROUP BY 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END
ORDER BY PlanIdPattern

-- Show a sample of the corrected lookup table
SELECT TOP 20 * 
FROM #CorrectedLookupPlanID
ORDER BY ControlNumber, Suffix, [State]

-- Compare the original and corrected tables for the problematic ControlNumber
SELECT 
    'Comparison for ControlNumber 0159375' AS Step,
    'Original Lookup' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #TempLookupPlanID
WHERE ControlNumber = '0159375'

UNION ALL

SELECT 
    'Comparison for ControlNumber 0159375' AS Step,
    'Corrected Lookup' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #CorrectedLookupPlanID
WHERE ControlNumber = '0159375'
ORDER BY TableType, Suffix, [State]


-- Create a master mapping table for PlanIds (this would ideally be a permanent table)
DROP TABLE IF EXISTS #PlanIdMapping
CREATE TABLE #PlanIdMapping
(
    StringPlanId varchar(50),
    NumericPlanId varchar(50),
    Description varchar(100)
)

-- Populate with known mappings
INSERT INTO #PlanIdMapping
VALUES 
('CMAPOS10', '00100', 'Converted from CMAPOS10'),
('CMAPOS11', '10100', 'Converted from CMAPOS11'),
('CMAPOS12', '20100', 'Converted from CMAPOS12'),
('CMAPOS13', '30100', 'Converted from CMAPOS13'),
('CMAPOS14', '40100', 'Converted from CMAPOS14'),
('CMAPOS15', '50100', 'Converted from CMAPOS15'),
('CMAPOS16', '60100', 'Converted from CMAPOS16'),
('CMAPOS17', '70100', 'Converted from CMAPOS17'),
('CMAEPO10', '00100', 'Converted from CMAEPO10'),
('CMAEPO11', '10100', 'Converted from CMAEPO11'),
('CMAEPO12', '20100', 'Converted from CMAEPO12'),
('CMAEPO13', '30100', 'Converted from CMAEPO13'),
('CMAEPO14', '40100', 'Converted from CMAEPO14'),
('CMAEPO15', '50100', 'Converted from CMAEPO15')

-- Create a staging table for verification
DROP TABLE IF EXISTS #StagingVerification
CREATE TABLE #StagingVerification
(
    ControlNumber varchar(50),
    Suffix varchar(50),
    Network varchar(50),
    [State] varchar(50),
    IsCoverageBased varchar(50),
    CoverageRules varchar(50),
    PlanId varchar(50),
    DepAge30Flag varchar(2),
    SourceTable varchar(20),
    ConversionNotes varchar(200)
)

-- Step 1: Insert all records from the extract table (this will be our base)
INSERT INTO #StagingVerification
SELECT 
    ControlNumber,
    Suffix,
    Network,
    [State],
    IsCoverageBased,
    CoverageRules,
    PlanId,
    DepAge30Flag,
    'Extract' AS SourceTable,
    'Original extract data' AS ConversionNotes
FROM #AccountStructurePlanIDExtract

-- Step 2: For records in the lookup table that don't exist in the extract table, add them
-- But convert string-based PlanIds to numeric using our mapping
INSERT INTO #StagingVerification
SELECT 
    la.ControlNumber,
    la.Suffix,
    la.Network,
    la.[State],
    la.IsCoverageBased,
    la.CoverageRules,
    -- Convert string-based PlanIds using our mapping
    ISNULL(m.NumericPlanId, 
        CASE 
            WHEN la.PlanId LIKE '%[^0-9]%' THEN '00000'  -- Default for unknown string PlanIds
            ELSE la.PlanId
        END
    ) AS PlanId,
    la.DepAge30Flag,
    'Lookup' AS SourceTable,
    CASE 
        WHEN m.StringPlanId IS NOT NULL THEN 'Converted from ' + la.PlanId + ' using mapping'
        WHEN la.PlanId LIKE '%[^0-9]%' THEN 'Unknown string PlanId - set to default'
        ELSE 'Original lookup data'
    END AS ConversionNotes
FROM #TempLookupPlanID la
LEFT JOIN #PlanIdMapping m ON la.PlanId = m.StringPlanId
LEFT JOIN #AccountStructurePlanIDExtract ase
    ON la.ControlNumber = ase.ControlNumber
    AND la.Suffix = ase.Suffix
    AND la.[State] = ase.[State]
WHERE ase.ControlNumber IS NULL

-- Step 3: Check for any remaining string-based PlanIds
SELECT 
    'Remaining string-based PlanIds' AS Step,
    ControlNumber,
    Suffix,
    [State],
    PlanId AS OriginalPlanId,
    ConversionNotes
FROM #StagingVerification
WHERE PlanId LIKE '%[^0-9]%'
ORDER BY ControlNumber, Suffix, [State]

-- Step 4: Create the final corrected table
DROP TABLE IF EXISTS #FinalCorrectedLookup
CREATE TABLE #FinalCorrectedLookup
(
    ControlNumber varchar(50),
    Suffix varchar(50),
    Network varchar(50),
    [State] varchar(50),
    IsCoverageBased varchar(50),
    CoverageRules varchar(50),
    PlanId varchar(50),
    DepAge30Flag varchar(2),
    SourceTable varchar(20),
    ConversionNotes varchar(200)
)

-- Insert all records from staging, converting any remaining string-based PlanIds to default
INSERT INTO #FinalCorrectedLookup
SELECT 
    ControlNumber,
    Suffix,
    Network,
    [State],
    IsCoverageBased,
    CoverageRules,
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN '00000'  -- Final conversion for any remaining strings
        ELSE PlanId
    END AS PlanId,
    DepAge30Flag,
    SourceTable,
    ConversionNotes + CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN ' - Final conversion to default'
        ELSE ''
    END AS ConversionNotes
FROM #StagingVerification

-- Verification queries
SELECT 'Final corrected lookup table record count' AS Step, COUNT(*) AS RecordCount
FROM #FinalCorrectedLookup

-- Show PlanId patterns in the final table
SELECT 
    'PlanId patterns in final corrected lookup table' AS Step,
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END AS PlanIdPattern,
    COUNT(*) AS RecordCount
FROM #FinalCorrectedLookup
GROUP BY 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END
ORDER BY PlanIdPattern

-- Show records with default PlanIds for manual review
SELECT 
    'Records with default PlanIds (00000) - need review' AS Step,
    ControlNumber,
    Suffix,
    [State],
    Network,
    PlanId,
    SourceTable,
    ConversionNotes
FROM #FinalCorrectedLookup
WHERE PlanId = '00000'
ORDER BY ControlNumber, Suffix, [State]

-- Show a sample of the final corrected table
SELECT TOP 20 * 
FROM #FinalCorrectedLookup
ORDER BY ControlNumber, Suffix, [State]

-- Compare the original and final tables for the problematic ControlNumber
SELECT 
    'Final comparison for ControlNumber 0159375' AS Step,
    'Original Lookup' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #TempLookupPlanID
WHERE ControlNumber = '0159375'

UNION ALL

SELECT 
    'Final comparison for ControlNumber 0159375' AS Step,
    'Final Corrected' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #FinalCorrectedLookup
WHERE ControlNumber = '0159375'
ORDER BY TableType, Suffix, [State]

-- Create a summary report
SELECT 
    'Summary Report' AS Step,
    'Original Lookup Records' AS Metric,
    COUNT(*) AS Value
FROM #TempLookupPlanID

UNION ALL

SELECT 
    'Summary Report' AS Step,
    'Original Extract Records' AS Metric,
    COUNT(*) AS Value
FROM #AccountStructurePlanIDExtract

UNION ALL

SELECT 
    'Summary Report' AS Step,
    'Final Corrected Records' AS Metric,
    COUNT(*) AS Value
FROM #FinalCorrectedLookup

UNION ALL

SELECT 
    'Summary Report' AS Step,
    'Records with Default PlanId (00000)' AS Metric,
    COUNT(*) AS Value
FROM #FinalCorrectedLookup
WHERE PlanId = '00000'

UNION ALL

SELECT 
    'Summary Report' AS Step,
    'Records from Extract Table' AS Metric,
    COUNT(*) AS Value
FROM #FinalCorrectedLookup
WHERE SourceTable = 'Extract'

UNION ALL

SELECT 
    'Summary Report' AS Step,
    'Records from Lookup Table' AS Metric,
    COUNT(*) AS Value
FROM #FinalCorrectedLookup
WHERE SourceTable = 'Lookup'

ORDER BY Metric

select * from [Aetna].[AetnaStructure_USStateAbbreviation] where Abbreviation = 'GA'














-- First, let's examine the Master table structure and extract state information
DROP TABLE IF EXISTS #MasterData
CREATE TABLE #MasterData
(
    ID int,
    SegmentID varchar(10),
    MaintenanceTypeCode varchar(10),
    MaintenanceReasonCode varchar(10),
    InsuranceLineCode varchar(10),
    ELR varchar(10),
    ControlNumber varchar(50),
    Suffix varchar(50),
    Account varchar(50),
    [Plan] varchar(50),
    ClaimOffice varchar(50),
    CoverageLevelCode varchar(10),
    AccountName varchar(100),
    PlanFullDescription varchar(500),
    State varchar(10),
    PlanDescription varchar(200),
    Network varchar(50),
    RateBand varchar(10),
    ActiveCobraFlag varchar(10),
    DepAge30Flag varchar(2),
    LastProcessedOn datetime
)

-- Populate Master data
INSERT INTO #MasterData
SELECT * 
FROM Aetna.AetnaStructure_Master

-- Extract state information from PlanFullDescription
DROP TABLE IF EXISTS #MasterWithState
CREATE TABLE #MasterWithState
(
    ID int,
    ControlNumber varchar(50),
    Suffix varchar(50),
    Account varchar(50),
    [Plan] varchar(50),
    PlanFullDescription varchar(500),
    ExtractedState varchar(100),
    StateAbbreviation varchar(10),
    Network varchar(50),
    DepAge30Flag varchar(2)
)

-- Extract state information and map to abbreviations
INSERT INTO #MasterWithState
SELECT 
    m.ID,
    m.ControlNumber,
    m.Suffix,
    m.Account,
    m.[Plan],
    m.PlanFullDescription,
    -- Extract state name from PlanFullDescription (between '-' and next '-')
    CASE 
        WHEN CHARINDEX(' - ', m.PlanFullDescription) > 0 
        THEN SUBSTRING(m.PlanFullDescription, 
                      CHARINDEX(' - ', m.PlanFullDescription) + 3, 
                      CASE 
                          WHEN CHARINDEX(' - ', m.PlanFullDescription, CHARINDEX(' - ', m.PlanFullDescription) + 3) > 0
                          THEN CHARINDEX(' - ', m.PlanFullDescription, CHARINDEX(' - ', m.PlanFullDescription) + 3) - (CHARINDEX(' - ', m.PlanFullDescription) + 3)
                          ELSE 100
                      END)
        ELSE NULL
    END AS ExtractedState,
    -- Map to state abbreviation
    s.Abbreviation,
    m.Network,
    m.DepAge30Flag
FROM #MasterData m
LEFT JOIN Aetna.AetnaStructure_USStateAbbreviation s 
    ON m.PlanFullDescription LIKE '%' + s.USStates + '%'

-- Create a normalized PlanId mapping from Master data
DROP TABLE IF EXISTS #MasterPlanIdMapping
CREATE TABLE #MasterPlanIdMapping
(
    ControlNumber varchar(50),
    NormalizedSuffix varchar(10),  -- Remove leading zeros
    StateAbbreviation varchar(10),
    PlanId varchar(50),
    Network varchar(50),
    DepAge30Flag varchar(2)
)

INSERT INTO #MasterPlanIdMapping
SELECT DISTINCT
    ControlNumber,
    -- Normalize suffix by removing leading zeros
    CASE 
        WHEN ISNUMERIC(Suffix) = 1 THEN CAST(CAST(Suffix AS int) AS varchar(10))
        ELSE Suffix
    END AS NormalizedSuffix,
    StateAbbreviation,
    [Plan],
    Network,
    DepAge30Flag
FROM #MasterWithState
WHERE [Plan] IS NOT NULL AND [Plan] <> ''

-- Now create a corrected lookup table using Master data as the primary source
DROP TABLE IF EXISTS #MasterCorrectedLookup
CREATE TABLE #MasterCorrectedLookup
(
    ControlNumber varchar(50),
    Suffix varchar(50),
    Network varchar(50),
    [State] varchar(50),
    IsCoverageBased varchar(50),
    CoverageRules varchar(50),
    PlanId varchar(50),
    DepAge30Flag varchar(2),
    SourceTable varchar(20),
    ConversionNotes varchar(200)
)

select * from edi.aETNA.AetnaStructure_Master

-- Step 1: Use Master data as the primary source
INSERT INTO #MasterCorrectedLookup
SELECT 
    m.ControlNumber,
    m.Suffix,
    m.Network,
    m.StateAbbreviation AS [State],
    '0' AS IsCoverageBased,  -- Default values
    'N' AS CoverageRules,     -- Default values
    m.PlanId,
    m.DepAge30Flag,
    'Master' AS SourceTable,
    'From Master table' AS ConversionNotes
FROM #MasterPlanIdMapping m

-- Step 2: Add records from extract table that don't exist in Master
INSERT INTO #MasterCorrectedLookup
SELECT 
    e.ControlNumber,
    e.Suffix,
    e.Network,
    e.[State],
    e.IsCoverageBased,
    e.CoverageRules,
    e.PlanId,
    e.DepAge30Flag,
    'Extract' AS SourceTable,
    'From extract table (not in Master)' AS ConversionNotes
FROM #AccountStructurePlanIDExtract e
WHERE NOT EXISTS (
    SELECT 1 FROM #MasterPlanIdMapping m
    WHERE m.ControlNumber = e.ControlNumber
    AND m.NormalizedSuffix = CASE 
        WHEN ISNUMERIC(e.Suffix) = 1 THEN CAST(CAST(e.Suffix AS int) AS varchar(10))
        ELSE e.Suffix
    END
    AND (m.StateAbbreviation = e.[State] OR m.StateAbbreviation IS NULL)
)

-- Step 3: Add records from lookup table that don't exist in Master or extract
-- Convert string-based PlanIds using our mapping
INSERT INTO #MasterCorrectedLookup
SELECT 
    l.ControlNumber,
    l.Suffix,
    l.Network,
    l.[State],
    l.IsCoverageBased,
    l.CoverageRules,
    -- Convert string-based PlanIds using our mapping
    CASE 
        WHEN l.PlanId LIKE '%[^0-9]%' THEN 
            CASE 
                WHEN l.PlanId = 'CMAPOS10' THEN '00100'
                WHEN l.PlanId = 'CMAPOS11' THEN '10100'
                WHEN l.PlanId = 'CMAPOS12' THEN '20100'
                WHEN l.PlanId = 'CMAPOS13' THEN '30100'
                WHEN l.PlanId = 'CMAPOS14' THEN '40100'
                WHEN l.PlanId = 'CMAPOS15' THEN '50100'
                WHEN l.PlanId = 'CMAEPO10' THEN '00100'
                WHEN l.PlanId = 'CMAEPO11' THEN '10100'
                WHEN l.PlanId = 'CMAEPO12' THEN '20100'
                WHEN l.PlanId = 'CMAEPO13' THEN '30100'
                WHEN l.PlanId = 'CMAEPO14' THEN '40100'
                WHEN l.PlanId = 'CMAEPO15' THEN '50100'
                ELSE '00000'
            END
        ELSE l.PlanId
    END AS PlanId,
    l.DepAge30Flag,
    'Lookup' AS SourceTable,
    CASE 
        WHEN l.PlanId LIKE '%[^0-9]%' THEN 'Converted from ' + l.PlanId
        ELSE 'From lookup table (not in Master or extract)'
    END AS ConversionNotes
FROM #TempLookupPlanID l
WHERE NOT EXISTS (
    SELECT 1 FROM #MasterPlanIdMapping m
    WHERE m.ControlNumber = l.ControlNumber
    AND m.NormalizedSuffix = CASE 
        WHEN ISNUMERIC(l.Suffix) = 1 THEN CAST(CAST(l.Suffix AS int) AS varchar(10))
        ELSE l.Suffix
    END
    AND (m.StateAbbreviation = l.[State] OR m.StateAbbreviation IS NULL)
)
AND NOT EXISTS (
    SELECT 1 FROM #AccountStructurePlanIDExtract e
    WHERE e.ControlNumber = l.ControlNumber
    AND e.Suffix = l.Suffix
    AND e.[State] = l.[State]
)

-- Verification queries
SELECT 'Master-corrected lookup table record count' AS Step, COUNT(*) AS RecordCount
FROM #MasterCorrectedLookup

-- Show PlanId patterns in the master-corrected table
SELECT 
    'PlanId patterns in master-corrected lookup table' AS Step,
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END AS PlanIdPattern,
    COUNT(*) AS RecordCount
FROM #MasterCorrectedLookup
GROUP BY 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END
ORDER BY PlanIdPattern

-- Show records with default PlanIds for manual review
SELECT 
    'Records with default PlanIds (00000) - need review' AS Step,
    ControlNumber,
    Suffix,
    [State],
    Network,
    PlanId,
    SourceTable,
    ConversionNotes
FROM #MasterCorrectedLookup
WHERE PlanId = '00000'
ORDER BY ControlNumber, Suffix, [State]

-- Show a sample of the master-corrected table
SELECT TOP 20 * 
FROM #MasterCorrectedLookup
ORDER BY ControlNumber, Suffix, [State]

-- Compare the original and master-corrected tables for the problematic ControlNumber
SELECT 
    'Master-based comparison for ControlNumber 0159375' AS Step,
    'Original Lookup' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #TempLookupPlanID
WHERE ControlNumber = '0159375'

UNION ALL

SELECT 
    'Master-based comparison for ControlNumber 0159375' AS Step,
    'Master Corrected' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #MasterCorrectedLookup
WHERE ControlNumber = '0159375'
ORDER BY TableType, Suffix, [State]


select * from edi.aETNA.AetnaStructure_Master
select  * from [Aetna].[AccountStructure_PlanID_Extract]



-- Drop and recreate MasterData with larger State column
DROP TABLE IF EXISTS #MasterData;
CREATE TABLE #MasterData
(
    ID int,
    SegmentID varchar(10),
    MaintenanceTypeCode varchar(10),
    MaintenanceReasonCode varchar(10),
    InsuranceLineCode varchar(10),
    ELR varchar(10),
    ControlNumber varchar(50),
    Suffix varchar(50),
    Account varchar(50),
    [Plan] varchar(50),
    ClaimOffice varchar(50),
    CoverageLevelCode varchar(10),
    AccountName varchar(200),
    PlanFullDescription varchar(1000),
    State varchar(100),              -- increased from 10 ? 100
    PlanDescription varchar(500),
    Network varchar(100),
    RateBand varchar(20),
    ActiveCobraFlag varchar(100),    -- increased from 10 ? 100
    DepAge30Flag varchar(10),
    LastProcessedOn datetime
);


-- Load from Master
INSERT INTO #MasterData
SELECT *
FROM Aetna.AetnaStructure_Master;

----------------------------------------------------------
-- Extract and map states properly
----------------------------------------------------------
DROP TABLE IF EXISTS #MasterWithState;
CREATE TABLE #MasterWithState
(
    ID int,
    ControlNumber varchar(50),
    Suffix varchar(50),
    Account varchar(50),
    [Plan] varchar(50),
    PlanFullDescription varchar(1000),
    ExtractedState varchar(100),
    StateAbbreviation varchar(10),
    Network varchar(50),
    DepAge30Flag varchar(2)
);

INSERT INTO #MasterWithState
SELECT 
    m.ID,
    m.ControlNumber,
    m.Suffix,
    m.Account,
    m.[Plan],
    m.PlanFullDescription,
    -- Take the first word/phrase before " - " as ExtractedState
    LTRIM(RTRIM(
        CASE 
            WHEN CHARINDEX(' - ', m.PlanFullDescription) > 0 
            THEN LEFT(m.PlanFullDescription, CHARINDEX(' - ', m.PlanFullDescription)-1)
            ELSE NULL
        END
    )) AS ExtractedState,
    s.Abbreviation,    -- official 2-letter state code from lookup
    m.Network,
    m.DepAge30Flag
FROM #MasterData m
LEFT JOIN Aetna.AetnaStructure_USStateAbbreviation s 
    ON m.PlanFullDescription LIKE '%' + s.USStates + '%';

----------------------------------------------------------
-- Normalize PlanId mapping
----------------------------------------------------------
DROP TABLE IF EXISTS #MasterPlanIdMapping;
CREATE TABLE #MasterPlanIdMapping
(
    ControlNumber varchar(50),
    NormalizedSuffix varchar(20),  
    StateAbbreviation varchar(10),
    PlanId varchar(50),
    Network varchar(50),
    DepAge30Flag varchar(2)
);

INSERT INTO #MasterPlanIdMapping
SELECT DISTINCT
    ControlNumber,
    -- Normalize suffix (strip leading zeros)
    CASE 
        WHEN ISNUMERIC(Suffix) = 1 
            THEN CAST(CAST(Suffix AS int) AS varchar(20))
        ELSE Suffix
    END AS NormalizedSuffix,
    StateAbbreviation,
    [Plan],
    Network,
    DepAge30Flag
FROM #MasterWithState
WHERE [Plan] IS NOT NULL AND [Plan] <> '';

----------------------------------------------------------
-- Create master-corrected lookup table
----------------------------------------------------------
DROP TABLE IF EXISTS #MasterCorrectedLookup;
CREATE TABLE #MasterCorrectedLookup
(
    ControlNumber varchar(50),
    Suffix varchar(50),
    Network varchar(50),
    [State] varchar(50),
    IsCoverageBased varchar(10),
    CoverageRules varchar(10),
    PlanId varchar(50),
    DepAge30Flag varchar(2),
    SourceTable varchar(20),
    ConversionNotes varchar(200)
);

-- Step 1: From Master
INSERT INTO #MasterCorrectedLookup
SELECT 
    m.ControlNumber,
    m.NormalizedSuffix AS Suffix,
    m.Network,
    m.StateAbbreviation AS [State],
    '0' AS IsCoverageBased, 
    'N' AS CoverageRules,     
    m.PlanId,
    m.DepAge30Flag,
    'Master' AS SourceTable,
    'From Master table' AS ConversionNotes
FROM #MasterPlanIdMapping m;

-- Step 2: From Extract (not in Master)
INSERT INTO #MasterCorrectedLookup
SELECT 
    e.ControlNumber,
    e.Suffix,
    e.Network,
    e.[State],
    e.IsCoverageBased,
    e.CoverageRules,
    e.PlanId,
    e.DepAge30Flag,
    'Extract' AS SourceTable,
    'From extract table (not in Master)' AS ConversionNotes
FROM [Aetna].[AccountStructure_PlanID_Extract] e
WHERE NOT EXISTS (
    SELECT 1 
    FROM #MasterPlanIdMapping m
    WHERE m.ControlNumber = e.ControlNumber
      AND m.NormalizedSuffix = 
            CASE WHEN ISNUMERIC(e.Suffix) = 1 
                 THEN CAST(CAST(e.Suffix AS int) AS varchar(20))
                 ELSE e.Suffix END
      AND (m.StateAbbreviation = e.[State] OR m.StateAbbreviation IS NULL)
);

-- Step 3: From Lookup (not in Master or Extract)
-- (this assumes #TempLookupPlanID exists already)
INSERT INTO #MasterCorrectedLookup
SELECT 
    l.ControlNumber,
    l.Suffix,
    l.Network,
    l.[State],
    l.IsCoverageBased,
    l.CoverageRules,
    CASE 
        WHEN l.PlanId LIKE '%[^0-9]%' THEN 
            CASE l.PlanId
                WHEN 'CMAPOS10' THEN '00100'
                WHEN 'CMAPOS11' THEN '10100'
                WHEN 'CMAPOS12' THEN '20100'
                WHEN 'CMAPOS13' THEN '30100'
                WHEN 'CMAPOS14' THEN '40100'
                WHEN 'CMAPOS15' THEN '50100'
                WHEN 'CMAEPO10' THEN '00100'
                WHEN 'CMAEPO11' THEN '10100'
                WHEN 'CMAEPO12' THEN '20100'
                WHEN 'CMAEPO13' THEN '30100'
                WHEN 'CMAEPO14' THEN '40100'
                WHEN 'CMAEPO15' THEN '50100'
                ELSE '00000'
            END
        ELSE l.PlanId
    END AS PlanId,
    l.DepAge30Flag,
    'Lookup' AS SourceTable,
    CASE 
        WHEN l.PlanId LIKE '%[^0-9]%' THEN 'Converted from ' + l.PlanId
        ELSE 'From lookup table (not in Master or extract)'
    END AS ConversionNotes
FROM #TempLookupPlanID l
WHERE NOT EXISTS (
    SELECT 1 
    FROM #MasterPlanIdMapping m
    WHERE m.ControlNumber = l.ControlNumber
      AND m.NormalizedSuffix = 
            CASE WHEN ISNUMERIC(l.Suffix) = 1 
                 THEN CAST(CAST(l.Suffix AS int) AS varchar(20))
                 ELSE l.Suffix END
      AND (m.StateAbbreviation = l.[State] OR m.StateAbbreviation IS NULL)
)
AND NOT EXISTS (
    SELECT 1 
    FROM [Aetna].[AccountStructure_PlanID_Extract] e
    WHERE e.ControlNumber = l.ControlNumber
      AND e.Suffix = l.Suffix
      AND e.[State] = l.[State]
);

----------------------------------------------------------
-- Validation queries
----------------------------------------------------------

-- 1. Count
SELECT 'Master-corrected lookup table record count' AS Step, COUNT(*) AS RecordCount
FROM #MasterCorrectedLookup;

-- 2. PlanId patterns
SELECT 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END AS PlanIdPattern,
    COUNT(*) AS RecordCount
FROM #MasterCorrectedLookup
GROUP BY 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END;

-- 3. Default PlanIds
SELECT *
FROM #MasterCorrectedLookup
WHERE PlanId = '00000'
ORDER BY ControlNumber, Suffix, [State];

-- 4. Sample
SELECT TOP 20 * 
FROM #MasterCorrectedLookup
ORDER BY ControlNumber, Suffix, [State];








-- First, let's examine what string-based PlanIds we actually have in the lookup table
SELECT 
    'String-based PlanIds in lookup table' AS Analysis,
    PlanId,
    COUNT(*) AS Count
FROM #TempLookupPlanID
WHERE PlanId LIKE '%[^0-9]%' AND PlanId IS NOT NULL
GROUP BY PlanId
ORDER BY PlanId;

-- Create a more comprehensive mapping table for string-based PlanIds
DROP TABLE IF EXISTS #ComprehensivePlanIdMapping;
CREATE TABLE #ComprehensivePlanIdMapping
(
    StringPlanId varchar(50),
    NumericPlanId varchar(50),
    Description varchar(100)
);

-- Populate with all known mappings, including patterns
INSERT INTO #ComprehensivePlanIdMapping
VALUES 
-- Original mappings
('CMAPOS10', '00100', 'Converted from CMAPOS10'),
('CMAPOS11', '10100', 'Converted from CMAPOS11'),
('CMAPOS12', '20100', 'Converted from CMAPOS12'),
('CMAPOS13', '30100', 'Converted from CMAPOS13'),
('CMAPOS14', '40100', 'Converted from CMAPOS14'),
('CMAPOS15', '50100', 'Converted from CMAPOS15'),
('CMAEPO10', '00100', 'Converted from CMAEPO10'),
('CMAEPO11', '10100', 'Converted from CMAEPO11'),
('CMAEPO12', '20100', 'Converted from CMAEPO12'),
('CMAEPO13', '30100', 'Converted from CMAEPO13'),
('CMAEPO14', '40100', 'Converted from CMAEPO14'),
('CMAEPO15', '50100', 'Converted from CMAEPO15'),
-- Additional mappings based on what we found
('CMAPOS16', '60100', 'Converted from CMAPOS16'),
('CMAPLAN11', '10100', 'Converted from CMAPLAN11'),
('CMAPLAN12', '20100', 'Converted from CMAPLAN12'),
('CMAPLAN14', '40100', 'Converted from CMAPLAN14'),
('CMAPLAN17', '70100', 'Converted from CMAPLAN17'),
('CMAEPO16', '60100', 'Converted from CMAEPO16');

-- Let's also check if there's a pattern we can use for automatic conversion
-- For example, if CMAPOSXX maps to XX100 (where XX is a 2-digit number)
-- Create a pattern-based mapping for any remaining string-based PlanIds
DROP TABLE IF EXISTS #PatternBasedMapping;
CREATE TABLE #PatternBasedMapping
(
    StringPlanId varchar(50),
    NumericPlanId varchar(50),
    ConversionMethod varchar(50)
);

-- Insert pattern-based conversions
INSERT INTO #PatternBasedMapping
SELECT 
    PlanId AS StringPlanId,
    CASE 
        -- Pattern: CMAPOSXX where XX is a number -> XX100
        WHEN PlanId LIKE 'CMAPOS%' AND SUBSTRING(PlanId, 7, 2) LIKE '[0-9][0-9]' 
            THEN SUBSTRING(PlanId, 7, 2) + '100'
        -- Pattern: CMAEPOXX where XX is a number -> XX100
        WHEN PlanId LIKE 'CMAEPO%' AND SUBSTRING(PlanId, 7, 2) LIKE '[0-9][0-9]' 
            THEN SUBSTRING(PlanId, 7, 2) + '100'
        -- Pattern: CMAPLANXX where XX is a number -> XX100
        WHEN PlanId LIKE 'CMAPLAN%' AND SUBSTRING(PlanId, 7, 2) LIKE '[0-9][0-9]' 
            THEN SUBSTRING(PlanId, 7, 2) + '100'
        ELSE '00000'
    END AS NumericPlanId,
    'Pattern-based conversion' AS ConversionMethod
FROM #TempLookupPlanID
WHERE PlanId LIKE '%[^0-9]%' 
AND PlanId IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM #ComprehensivePlanIdMapping m 
    WHERE m.StringPlanId = PlanId
);

-- Combine explicit and pattern-based mappings
DROP TABLE IF EXISTS #CombinedPlanIdMapping;
CREATE TABLE #CombinedPlanIdMapping
(
    StringPlanId varchar(50),
    NumericPlanId varchar(50),
    Description varchar(100)
);

INSERT INTO #CombinedPlanIdMapping
SELECT StringPlanId, NumericPlanId, Description FROM #ComprehensivePlanIdMapping
UNION ALL
SELECT StringPlanId, NumericPlanId, ConversionMethod FROM #PatternBasedMapping;

-- Now let's improve our Master data extraction
-- Check if we're missing state information
SELECT 
    'Master records with NULL State' AS Analysis,
    COUNT(*) AS Count
FROM #MasterData
WHERE State IS NULL OR State = '';

-- Let's try a different approach to extract state information
DROP TABLE IF EXISTS #ImprovedMasterWithState;
CREATE TABLE #ImprovedMasterWithState
(
    ID int,
    ControlNumber varchar(50),
    Suffix varchar(50),
    Account varchar(50),
    [Plan] varchar(50),
    PlanFullDescription varchar(1000),
    ExtractedState varchar(100),
    StateAbbreviation varchar(10),
    Network varchar(50),
    DepAge30Flag varchar(2)
);

-- Improved state extraction
INSERT INTO #ImprovedMasterWithState
SELECT 
    m.ID,
    m.ControlNumber,
    m.Suffix,
    m.Account,
    m.[Plan],
    m.PlanFullDescription,
    -- Try multiple methods to extract state
    CASE 
        -- Method 1: Look for state abbreviation pattern (XX - where XX is uppercase letters)
        WHEN m.PlanFullDescription LIKE '% [A-Z][A-Z] -%' THEN
            SUBSTRING(m.PlanFullDescription, 
                      PATINDEX('% [A-Z][A-Z] -%', m.PlanFullDescription) + 1, 2)
        -- Method 2: Look for state name in the description
        WHEN EXISTS (
            SELECT 1 FROM Aetna.AetnaStructure_USStateAbbreviation s 
            WHERE m.PlanFullDescription LIKE '%' + s.USStates + '%'
        ) THEN (
            SELECT TOP 1 s.Abbreviation 
            FROM Aetna.AetnaStructure_USStateAbbreviation s 
            WHERE m.PlanFullDescription LIKE '%' + s.USStates + '%'
        )
        ELSE NULL
    END AS ExtractedState,
    -- Map to state abbreviation
    CASE 
        WHEN m.PlanFullDescription LIKE '% [A-Z][A-Z] -%' THEN
            SUBSTRING(m.PlanFullDescription, 
                      PATINDEX('% [A-Z][A-Z] -%', m.PlanFullDescription) + 1, 2)
        WHEN EXISTS (
            SELECT 1 FROM Aetna.AetnaStructure_USStateAbbreviation s 
            WHERE m.PlanFullDescription LIKE '%' + s.USStates + '%'
        ) THEN (
            SELECT TOP 1 s.Abbreviation 
            FROM Aetna.AetnaStructure_USStateAbbreviation s 
            WHERE m.PlanFullDescription LIKE '%' + s.USStates + '%'
        )
        ELSE NULL
    END AS StateAbbreviation,
    m.Network,
    m.DepAge30Flag
FROM #MasterData m;

-- Now recreate the MasterPlanIdMapping with improved state extraction
DROP TABLE IF EXISTS #ImprovedMasterPlanIdMapping;
CREATE TABLE #ImprovedMasterPlanIdMapping
(
    ControlNumber varchar(50),
    NormalizedSuffix varchar(20),  
    StateAbbreviation varchar(10),
    PlanId varchar(50),
    Network varchar(50),
    DepAge30Flag varchar(2)
);

INSERT INTO #ImprovedMasterPlanIdMapping
SELECT DISTINCT
    ControlNumber,
    -- Normalize suffix (strip leading zeros)
    CASE 
        WHEN ISNUMERIC(Suffix) = 1 
            THEN CAST(CAST(Suffix AS int) AS varchar(20))
        ELSE Suffix
    END AS NormalizedSuffix,
    StateAbbreviation,
    [Plan],
    Network,
    DepAge30Flag
FROM #ImprovedMasterWithState
WHERE [Plan] IS NOT NULL AND [Plan] <> '';

-- Now create the final corrected lookup table
DROP TABLE IF EXISTS #FinalMasterCorrectedLookup;
CREATE TABLE #FinalMasterCorrectedLookup
(
    ControlNumber varchar(50),
    Suffix varchar(50),
    Network varchar(50),
    [State] varchar(50),
    IsCoverageBased varchar(10),
    CoverageRules varchar(10),
    PlanId varchar(50),
    DepAge30Flag varchar(2),
    SourceTable varchar(20),
    ConversionNotes varchar(200)
);

-- Step 1: From Master (improved)
INSERT INTO #FinalMasterCorrectedLookup
SELECT 
    m.ControlNumber,
    m.NormalizedSuffix AS Suffix,
    COALESCE(m.Network, 'NAT') AS Network,  -- Default network if NULL
    COALESCE(m.StateAbbreviation, 'AL') AS [State],  -- Default state if NULL
    '0' AS IsCoverageBased, 
    'N' AS CoverageRules,     
    m.PlanId,
    COALESCE(m.DepAge30Flag, '0') AS DepAge30Flag,  -- Default if NULL
    'Master' AS SourceTable,
    'From Master table' AS ConversionNotes
FROM #ImprovedMasterPlanIdMapping m;

-- Step 2: From Extract (not in Master)
INSERT INTO #FinalMasterCorrectedLookup
SELECT 
    e.ControlNumber,
    e.Suffix,
    e.Network,
    e.[State],
    e.IsCoverageBased,
    e.CoverageRules,
    e.PlanId,
    e.DepAge30Flag,
    'Extract' AS SourceTable,
    'From extract table (not in Master)' AS ConversionNotes
FROM [Aetna].[AccountStructure_PlanID_Extract] e
WHERE NOT EXISTS (
    SELECT 1 
    FROM #ImprovedMasterPlanIdMapping m
    WHERE m.ControlNumber = e.ControlNumber
      AND m.NormalizedSuffix = 
            CASE WHEN ISNUMERIC(e.Suffix) = 1 
                 THEN CAST(CAST(e.Suffix AS int) AS varchar(20))
                 ELSE e.Suffix END
      AND (m.StateAbbreviation = e.[State] OR m.StateAbbreviation IS NULL)
);

-- Step 3: From Lookup (not in Master or Extract) with improved conversion
INSERT INTO #FinalMasterCorrectedLookup
SELECT 
    l.ControlNumber,
    l.Suffix,
    COALESCE(l.Network, 'NAT') AS Network,  -- Default network if NULL
    COALESCE(l.[State], 'AL') AS [State],  -- Default state if NULL
    COALESCE(l.IsCoverageBased, '0') AS IsCoverageBased,  -- Default if NULL
    COALESCE(l.CoverageRules, 'N') AS CoverageRules,  -- Default if NULL
    -- Use our comprehensive mapping
    COALESCE(
        cm.NumericPlanId, 
        CASE 
            -- If we have a numeric PlanId, use it
            WHEN l.PlanId NOT LIKE '%[^0-9]%' THEN l.PlanId
            -- Default for unknown string PlanIds
            ELSE '00000'
        END
    ) AS PlanId,
    COALESCE(l.DepAge30Flag, '0') AS DepAge30Flag,  -- Default if NULL
    'Lookup' AS SourceTable,
    CASE 
        WHEN cm.StringPlanId IS NOT NULL THEN 'Converted from ' + l.PlanId + ' using mapping'
        WHEN l.PlanId LIKE '%[^0-9]%' THEN 'Unknown string PlanId - set to default'
        ELSE 'From lookup table (not in Master or extract)'
    END AS ConversionNotes
FROM #TempLookupPlanID l
LEFT JOIN #CombinedPlanIdMapping cm ON l.PlanId = cm.StringPlanId
WHERE NOT EXISTS (
    SELECT 1 
    FROM #ImprovedMasterPlanIdMapping m
    WHERE m.ControlNumber = l.ControlNumber
      AND m.NormalizedSuffix = 
            CASE WHEN ISNUMERIC(l.Suffix) = 1 
                 THEN CAST(CAST(l.Suffix AS int) AS varchar(20))
                 ELSE l.Suffix END
      AND (m.StateAbbreviation = l.[State] OR m.StateAbbreviation IS NULL)
)
AND NOT EXISTS (
    SELECT 1 
    FROM [Aetna].[AccountStructure_PlanID_Extract] e
    WHERE e.ControlNumber = l.ControlNumber
      AND e.Suffix = l.Suffix
      AND e.[State] = l.[State]
);

-- Validation queries
SELECT 'Final master-corrected lookup table record count' AS Step, COUNT(*) AS RecordCount
FROM #FinalMasterCorrectedLookup;

-- Show PlanId patterns
SELECT 
    'PlanId patterns in final master-corrected lookup table' AS Step,
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END AS PlanIdPattern,
    COUNT(*) AS RecordCount
FROM #FinalMasterCorrectedLookup
GROUP BY 
    CASE 
        WHEN PlanId LIKE '%[^0-9]%' THEN 'String-based'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9][0-9]' THEN '5-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9][0-9]' THEN '4-digit numeric'
        WHEN PlanId LIKE '[0-9][0-9][0-9]' THEN '3-digit numeric'
        ELSE 'Other pattern'
    END
ORDER BY PlanIdPattern;

-- Show records with default PlanIds
SELECT 
    'Records with default PlanIds (00000) - need review' AS Step,
    ControlNumber,
    Suffix,
    [State],
    Network,
    PlanId,
    SourceTable,
    ConversionNotes
FROM #FinalMasterCorrectedLookup
WHERE PlanId = '00000'
ORDER BY ControlNumber, Suffix, [State];

-- Show a sample of the final master-corrected table
SELECT TOP 20 * 
FROM #FinalMasterCorrectedLookup
ORDER BY ControlNumber, Suffix, [State];

-- Compare the original and final tables for the problematic ControlNumber
SELECT 
    'Final master-based comparison for ControlNumber 0159375' AS Step,
    'Original Lookup' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #TempLookupPlanID
WHERE ControlNumber = '0159375'

UNION ALL

SELECT 
    'Final master-based comparison for ControlNumber 0159375' AS Step,
    'Final Master Corrected' AS TableType,
    ControlNumber,
    Suffix,
    [State],
    PlanId
FROM #FinalMasterCorrectedLookup
WHERE ControlNumber = '0159375'
ORDER BY TableType, Suffix, [State];

-- Create a summary report
SELECT 
    'Final Master-based Summary Report' AS Step,
    'Original Lookup Records' AS Metric,
    COUNT(*) AS Value
FROM #TempLookupPlanID

UNION ALL

SELECT 
    'Final Master-based Summary Report' AS Step,
    'Original Extract Records' AS Metric,
    COUNT(*) AS Value
FROM [Aetna].[AccountStructure_PlanID_Extract]

UNION ALL

SELECT 
    'Final Master-based Summary Report' AS Step,
    'Final Master Corrected Records' AS Metric,
    COUNT(*) AS Value
FROM #FinalMasterCorrectedLookup

UNION ALL

SELECT 
    'Final Master-based Summary Report' AS Step,
    'Records with Default PlanId (00000)' AS Metric,
    COUNT(*) AS Value
FROM #FinalMasterCorrectedLookup
WHERE PlanId = '00000'

UNION ALL

SELECT 
    'Final Master-based Summary Report' AS Step,
    'Records from Master Table' AS Metric,
    COUNT(*) AS Value
FROM #FinalMasterCorrectedLookup
WHERE SourceTable = 'Master'

UNION ALL

SELECT 
    'Final Master-based Summary Report' AS Step,
    'Records from Extract Table' AS Metric,
    COUNT(*) AS Value
FROM #FinalMasterCorrectedLookup
WHERE SourceTable = 'Extract'

UNION ALL

SELECT 
    'Final Master-based Summary Report' AS Step,
    'Records from Lookup Table' AS Metric,
    COUNT(*) AS Value
FROM #FinalMasterCorrectedLookup
WHERE SourceTable = 'Lookup'

ORDER BY Metric;















IF OBJECT_ID('tempdb..#ParsedStagingData') IS NOT NULL DROP TABLE #ParsedStagingData;
IF OBJECT_ID('tempdb..#ImprovedMasterWithState') IS NOT NULL DROP TABLE #ImprovedMasterWithState;
IF OBJECT_ID('tempdb..#CompleteSourceMapping') IS NOT NULL DROP TABLE #CompleteSourceMapping;
IF OBJECT_ID('tempdb..#AllStringPlanIds') IS NOT NULL DROP TABLE #AllStringPlanIds;
IF OBJECT_ID('tempdb..#CompleteStringPlanIdMapping') IS NOT NULL DROP TABLE #CompleteStringPlanIdMapping;
IF OBJECT_ID('tempdb..#TempLookupPlanID') IS NOT NULL DROP TABLE #TempLookupPlanID;
IF OBJECT_ID('tempdb..#FinalCompleteLookup') IS NOT NULL DROP TABLE #FinalCompleteLookup;


-- ======================================================
-- 1) Parse staging HD04 robustly using XML-split
--    (HD04 example: '009+0259324+011+00026+10400+735')
-- ======================================================
CREATE TABLE #ParsedStagingData
(
    ID int,
    SheetName varchar(100),
    HD varchar(20),
    HD01 varchar(200),
    HD02 varchar(200),
    HD03 varchar(200),
    HD04 varchar(4000),
    HD05 varchar(200),
    ControlNumber varchar(50),
    Suffix varchar(50),
    Account varchar(50),
    PlanId varchar(50),
    ClaimOffice varchar(100),
    AccountName varchar(500),
    Description varchar(2000),
    StateName varchar(200),
    StateAbbreviation varchar(10),
    IsGarbage bit,
    ExtractTimeStamp datetime
);

INSERT INTO #ParsedStagingData (ID, SheetName, HD, HD01, HD02, HD03, HD04, HD05,
                               ControlNumber, Suffix, Account, PlanId, ClaimOffice,
                               AccountName, Description, StateName, StateAbbreviation,
                               IsGarbage, ExtractTimeStamp)
SELECT
    s.ID,
    s.SheetName,
    s.HD,
    s.HD01,
    s.HD02,
    s.HD03,
    s.HD04,
    s.HD05,
    -- parse using XML to get positional components
    LTRIM(RTRIM(NULLIF(x.item.value('(c[2]/text())[1]', 'varchar(100)'), ''))) AS ControlNumber,
    LTRIM(RTRIM(NULLIF(x.item.value('(c[3]/text())[1]', 'varchar(50)'), ''))) AS Suffix,
    LTRIM(RTRIM(NULLIF(x.item.value('(c[4]/text())[1]', 'varchar(50)'), ''))) AS Account,
    LTRIM(RTRIM(NULLIF(x.item.value('(c[5]/text())[1]', 'varchar(50)'), ''))) AS PlanId,
    LTRIM(RTRIM(NULLIF(x.item.value('(c[6]/text())[1]', 'varchar(50)'), ''))) AS ClaimOffice,
    s.AccountName,
    s.Description,
    -- StateName: text to left of first ' - ' in Description (trimmed)
    CASE WHEN CHARINDEX(' - ', s.Description) > 0 
         THEN LTRIM(RTRIM(LEFT(s.Description, CHARINDEX(' - ', s.Description) - 1)))
         ELSE NULL END AS StateName,
    -- Map to abbreviation using USStates mapping (first match)
    (
      SELECT TOP 1 a.Abbreviation
      FROM Aetna.AetnaStructure_USStateAbbreviation a
      WHERE s.Description LIKE '%' + a.USStates + '%'
    ) AS StateAbbreviation,
    s.IsGarbage,
    s.ExtractTimeStamp
FROM Aetna.AetnaStructure_Staging s
CROSS APPLY (
    SELECT TRY_CAST('<r><c>' + 
           REPLACE(
               REPLACE(REPLACE(ISNULL(s.HD04,''),'&','&amp;'),'<','<'), '+', '</c><c>') 
           + '</c></r>' AS XML) AS xmlCol
) AS xmlT
CROSS APPLY (
    SELECT xmlT.xmlCol AS item  -- ? FIXED: Only one column 'item'
) AS x
WHERE s.IsGarbage = 0
  AND s.HD04 IS NOT NULL;

-- ======================================================
-- 2) Build improved master-with-state (no truncation)
--    ensure columns are wide enough to hold full text
-- ======================================================
DROP TABLE IF EXISTS #ImprovedMasterWithState;
CREATE TABLE #ImprovedMasterWithState
(
    ID int,
    ControlNumber varchar(50),
    Suffix varchar(50),
    Account varchar(50),
    [Plan] varchar(50),
    PlanFullDescription varchar(2000),
    ExtractedState varchar(200),
    StateAbbreviation varchar(10),
    Network varchar(100),
    DepAge30Flag varchar(10)
);

INSERT INTO #ImprovedMasterWithState (ID, ControlNumber, Suffix, Account, [Plan], PlanFullDescription, ExtractedState, StateAbbreviation, Network, DepAge30Flag)
SELECT 
    m.ID,
    m.ControlNumber,
    m.Suffix,
    m.Account,
    m.[Plan],
    m.PlanFullDescription,
    -- Extract text before first ' - ' (safe for long names)
    CASE WHEN CHARINDEX(' - ', m.PlanFullDescription) > 0 
         THEN LTRIM(RTRIM(LEFT(m.PlanFullDescription, CHARINDEX(' - ', m.PlanFullDescription) - 1)))
         ELSE NULL END AS ExtractedState,
    s.Abbreviation,
    m.Network,
    m.DepAge30Flag
FROM Aetna.AetnaStructure_Master m
LEFT JOIN Aetna.AetnaStructure_USStateAbbreviation s
    ON m.PlanFullDescription LIKE '%' + s.USStates + '%';

-- ======================================================
-- 3) Build #CompleteSourceMapping from Master & Staging
-- ======================================================
CREATE TABLE #CompleteSourceMapping
(
    ControlNumber varchar(50),
    NormalizedSuffix varchar(20),
    StateAbbreviation varchar(10),
    PlanId varchar(50),
    Network varchar(50),
    DepAge30Flag varchar(2),
    SourceTable varchar(20),
    Description varchar(2000)
);

-- From Master
INSERT INTO #CompleteSourceMapping (ControlNumber, NormalizedSuffix, StateAbbreviation, PlanId, Network, DepAge30Flag, SourceTable, Description)
SELECT DISTINCT
    ControlNumber,
    CASE WHEN ISNUMERIC(Suffix) = 1 THEN CAST(CAST(Suffix AS int) AS varchar(20)) ELSE Suffix END AS NormalizedSuffix,
    StateAbbreviation,
    [Plan] AS PlanId,
    Network,
    DepAge30Flag,
    'Master',
    PlanFullDescription
FROM #ImprovedMasterWithState
WHERE [Plan] IS NOT NULL AND [Plan] <> '';

-- From Staging (parsed)
INSERT INTO #CompleteSourceMapping (ControlNumber, NormalizedSuffix, StateAbbreviation, PlanId, Network, DepAge30Flag, SourceTable, Description)
SELECT DISTINCT
    ControlNumber,
    CASE WHEN ISNUMERIC(Suffix) = 1 THEN CAST(CAST(Suffix AS int) AS varchar(20)) ELSE Suffix END AS NormalizedSuffix,
    StateAbbreviation,
    PlanId,
    -- Derive network from description heuristics (adjust as needed)
    CASE 
        WHEN Description LIKE '%OA EPO%' OR Description LIKE '%OPEN ACCESS%' OR Description LIKE '%OA%' THEN 'OA'
        WHEN Description LIKE '%HMO%' THEN 'HMO'
        WHEN Description LIKE '%POS%' THEN 'NATLMCPOS'
        WHEN Description LIKE '%EPO%' THEN 'NATLEPO'
        WHEN Description LIKE '%NOMA%' THEN 'NOMA'
        WHEN Description LIKE '%Nat%' OR Description LIKE '%NAT%' THEN 'Nat'
        ELSE NULL
    END AS Network,
    '0' AS DepAge30Flag,
    'Staging',
    Description
FROM #ParsedStagingData
WHERE PlanId IS NOT NULL AND PlanId <> '';

-- ======================================================
-- 4) Pull temp copy of current lookup (read-only)
-- ======================================================
SELECT * INTO #TempLookupPlanID
FROM EDI.Aetna.lookup_AccountStructure_PlanID;  -- safe read into temp

-- ======================================================
-- 5) Build mapping for string PlanIds
-- ======================================================
CREATE TABLE #AllStringPlanIds(StringPlanId varchar(50), Cnt int);
INSERT INTO #AllStringPlanIds(StringPlanId, Cnt)
SELECT PlanId, COUNT(*) FROM #TempLookupPlanID
WHERE PlanId IS NOT NULL AND PlanId LIKE '%[^0-9]%'
GROUP BY PlanId;

CREATE TABLE #CompleteStringPlanIdMapping(StringPlanId varchar(50), NumericPlanId varchar(50), MappingMethod varchar(50), ConfidenceLevel varchar(20));
-- explicit known mappings
INSERT INTO #CompleteStringPlanIdMapping (StringPlanId, NumericPlanId, MappingMethod, ConfidenceLevel)
VALUES
('CMAPOS10','00100','Explicit','High'),
('CMAPOS11','10100','Explicit','High'),
('CMAPOS12','20100','Explicit','High'),
('CMAPOS13','30100','Explicit','High'),
('CMAPOS14','40100','Explicit','High'),
('CMAPOS15','50100','Explicit','High'),
('CMAPOS16','60100','Explicit','High'),
('CMAPOS17','70100','Explicit','High'),
('CMAEPO10','00100','Explicit','High'),
('CMAEPO11','10100','Explicit','High'),
('CMAEPO12','20100','Explicit','High'),
('CMAEPO13','30100','Explicit','High'),
('CMAEPO14','40100','Explicit','High'),
('CMAEPO15','50100','Explicit','High'),
('CMAPLAN10','00100','Explicit','High'),
('CMAPLAN11','10100','Explicit','High'),
('CMAPLAN12','20100','Explicit','High'),
('CMAPLAN13','30100','Explicit','High'),
('CMAPLAN14','40100','Explicit','High'),
('CMAPLAN15','50100','Explicit','High'),
('CMAPLAN16','60100','Explicit','High'),
('CMAPLAN17','70100','Explicit','High'),
('CMAPLAN18','80100','Explicit','High');

-- pattern-based mapping for any remaining
INSERT INTO #CompleteStringPlanIdMapping (StringPlanId, NumericPlanId, MappingMethod, ConfidenceLevel)
SELECT a.StringPlanId,
       CASE 
         WHEN a.StringPlanId LIKE 'CMAPOS%' AND ISNUMERIC(SUBSTRING(a.StringPlanId,7,2)) = 1 THEN SUBSTRING(a.StringPlanId,7,2) + '100'
         WHEN a.StringPlanId LIKE 'CMAEPO%' AND ISNUMERIC(SUBSTRING(a.StringPlanId,7,2)) = 1 THEN SUBSTRING(a.StringPlanId,7,2) + '100'
         WHEN a.StringPlanId LIKE 'CMAPLAN%' AND ISNUMERIC(SUBSTRING(a.StringPlanId,7,2)) = 1 THEN SUBSTRING(a.StringPlanId,7,2) + '100'
         ELSE '00000' END AS NumericPlanId,
       'Pattern' AS MappingMethod,
       CASE 
         WHEN (a.StringPlanId LIKE 'CMAPOS%' OR a.StringPlanId LIKE 'CMAEPO%' OR a.StringPlanId LIKE 'CMAPLAN%') AND ISNUMERIC(SUBSTRING(a.StringPlanId,7,2)) = 1 THEN 'Medium'
         ELSE 'Low' END AS ConfidenceLevel
FROM #AllStringPlanIds a
WHERE NOT EXISTS (SELECT 1 FROM #CompleteStringPlanIdMapping m WHERE m.StringPlanId = a.StringPlanId);

-- ======================================================
-- 6) Build final combined temp lookup (#FinalCompleteLookup)
--    Priority: Master -> Staging -> Extract -> Existing Lookup (converted)
-- ======================================================
CREATE TABLE #FinalCompleteLookup
(
    ControlNumber varchar(50),
    Suffix varchar(50),
    Network varchar(100),
    [State] varchar(100),
    IsCoverageBased varchar(10),
    CoverageRules varchar(10),
    PlanId varchar(50),
    DepAge30Flag varchar(2),
    SourceTable varchar(20),
    ConversionNotes varchar(500)
);

-- 6.1 From CompleteSourceMapping (Master + Staging)
INSERT INTO #FinalCompleteLookup (ControlNumber, Suffix, Network, [State], IsCoverageBased, CoverageRules, PlanId, DepAge30Flag, SourceTable, ConversionNotes)
SELECT 
    c.ControlNumber,
    c.NormalizedSuffix,
    COALESCE(c.Network, 'Nat') AS Network,
    COALESCE(c.StateAbbreviation, NULL) AS [State],
    '0' AS IsCoverageBased,
    'N' AS CoverageRules,
    c.PlanId,
    COALESCE(c.DepAge30Flag, '0') AS DepAge30Flag,
    c.SourceTable,
    'From ' + c.SourceTable
FROM #CompleteSourceMapping c;

-- 6.2 From Extract if missing
INSERT INTO #FinalCompleteLookup (ControlNumber, Suffix, Network, [State], IsCoverageBased, CoverageRules, PlanId, DepAge30Flag, SourceTable, ConversionNotes)
SELECT e.ControlNumber, e.Suffix, e.Network, e.[State], e.IsCoverageBased, e.CoverageRules, e.PlanId, e.DepAge30Flag, 'Extract', 'From extract (not in Master/Staging)'
FROM Aetna.AccountStructure_PlanID_Extract e
WHERE NOT EXISTS (
    SELECT 1 FROM #FinalCompleteLookup f
    WHERE f.ControlNumber = e.ControlNumber
      AND f.Suffix = CASE WHEN ISNUMERIC(e.Suffix)=1 THEN CAST(CAST(e.Suffix AS int) AS varchar) ELSE e.Suffix END
      AND ISNULL(f.[State],'') = ISNULL(e.[State],'')
      AND ISNULL(f.PlanId,'') = ISNULL(e.PlanId,'')
);

-- 6.3 From existing lookup only if not present in final (convert string plan ids)
INSERT INTO #FinalCompleteLookup (ControlNumber, Suffix, Network, [State], IsCoverageBased, CoverageRules, PlanId, DepAge30Flag, SourceTable, ConversionNotes)
SELECT 
    l.ControlNumber,
    l.Suffix,
    COALESCE(l.Network, 'Nat'),
    l.[State],
    COALESCE(l.IsCoverageBased, '0'),
    COALESCE(l.CoverageRules, 'N'),
    COALESCE(m.NumericPlanId,
            CASE WHEN l.PlanId NOT LIKE '%[^0-9]%' THEN l.PlanId ELSE '00000' END),
    COALESCE(l.DepAge30Flag,'0'),
    'Lookup',
    CASE WHEN m.StringPlanId IS NOT NULL THEN 'Converted from ' + l.PlanId + ' ('+m.MappingMethod+')'
         WHEN l.PlanId LIKE '%[^0-9]%' THEN 'Unknown string -> default 00000'
         ELSE 'From lookup' END
FROM #TempLookupPlanID l
LEFT JOIN #CompleteStringPlanIdMapping m ON l.PlanId = m.StringPlanId
WHERE NOT EXISTS (
    SELECT 1 FROM #FinalCompleteLookup f
    WHERE f.ControlNumber = l.ControlNumber
      AND f.Suffix = l.Suffix
      AND ISNULL(f.[State],'') = ISNULL(l.[State],'')
      AND ISNULL(f.PlanId,'') = ISNULL(COALESCE(m.NumericPlanId, CASE WHEN l.PlanId NOT LIKE '%[^0-9]%' THEN l.PlanId ELSE '00000' END),'')
);

-- ======================================================
-- 7) Validation & Reports (inspect these results)
-- ======================================================

-- A) Counts
SELECT 'FinalComplete total' AS Step, COUNT(*) AS CountRows FROM #FinalCompleteLookup;
SELECT 'Original lookup rows (temp)' AS Step, COUNT(*) AS CountRows FROM #TempLookupPlanID;
SELECT 'AccountStructure_PlanID_Extract rows' AS Step, COUNT(*) AS CountRows FROM Aetna.AccountStructure_PlanID_Extract;

-- B) How many default PlanId '00000' (need manual review)
SELECT COUNT(*) AS DefaultPlan00_Count FROM #FinalCompleteLookup WHERE PlanId = '00000';

-- C) Sample rows that were NAT / NULL previously (string PlanIDs etc.)
SELECT TOP (200)
    f.ControlNumber, f.Suffix, f.Network, f.[State], f.PlanId, f.SourceTable, f.ConversionNotes
FROM #FinalCompleteLookup f
WHERE f.PlanId = '00000' OR f.SourceTable = 'Lookup'
ORDER BY f.ControlNumber, f.Suffix, f.[State];

-- D) Show where previous lookup had [State] IS NULL but now resolved
SELECT
    l.ControlNumber, l.Suffix, l.Network AS LookupNetwork, l.[State] AS LookupState, l.PlanId AS LookupPlan,
    f.Network AS FinalNetwork, f.[State] AS FinalState, f.PlanId AS FinalPlan, f.SourceTable
FROM #TempLookupPlanID l
LEFT JOIN #FinalCompleteLookup f
  ON l.ControlNumber = f.ControlNumber
 AND l.Suffix = f.Suffix
WHERE l.[State] IS NULL
ORDER BY l.ControlNumber, l.Suffix;

-- E) Show differences for a problematic control (example 0159375)
SELECT * FROM #TempLookupPlanID WHERE ControlNumber = '0159375' ORDER BY Suffix, [State], PlanId;
SELECT * FROM #FinalCompleteLookup WHERE ControlNumber = '0159375' ORDER BY Suffix, [State], PlanId;

-- F) Summary: plan id patterns in final
SELECT 
    CASE WHEN PlanId LIKE '%[^0-9]%' THEN 'String' WHEN LEN(PlanId)=5 AND PlanId NOT LIKE '%[^0-9]%' THEN '5-digit' ELSE 'Other' END AS Pattern,
    COUNT(*) AS Cnt
FROM #FinalCompleteLookup
GROUP BY CASE WHEN PlanId LIKE '%[^0-9]%' THEN 'String' WHEN LEN(PlanId)=5 AND PlanId NOT LIKE '%[^0-9]%' THEN '5-digit' ELSE 'Other' END
ORDER BY Pattern;

-- G) Quick spot-check: show rows that were NEW (present in extract but not in lookup)
SELECT e.ControlNumber, e.Suffix, e.Network, e.[State], e.PlanID, e.DepAge30Flag
FROM Aetna.AccountStructure_PlanID_Extract e
LEFT JOIN #TempLookupPlanID l
  ON l.ControlNumber = e.ControlNumber
 AND l.Suffix = e.Suffix
 AND l.Network = e.Network
 AND l.[State] = e.[State]
WHERE l.ControlNumber IS NULL
ORDER BY e.ControlNumber, e.Suffix, e.[State];








SELECT 
    ape.ID,
    ape.ControlNumber,
    ape.Suffix,
    ape.Network AS CurrentNetwork,
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        ELSE ape.Network
    END AS ProposedNetwork,
    ape.[State] AS CurrentState,
    usa.Abbreviation AS ProposedState,
    ape.PlanID,
    m.PlanFullDescription,
    m.PlanDescription
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
INNER JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND ape.Suffix = m.Suffix
    AND ape.PlanID = m.[Plan]
INNER JOIN [EDI].[Aetna].[AetnaStructure_USStateAbbreviation] usa
    ON m.PlanFullDescription LIKE usa.USStates + ' -%'
WHERE ape.Network = 'Nat';














-- PREVIEW: See how bad rows in AccountStructure_PlanID_Extract will be fixed using AetnaStructure_Master
SELECT 
    ape.ID,
    ape.ControlNumber,
    ape.Suffix,
    ape.Network AS CurrentNetwork,
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        ELSE ape.Network
    END AS ProposedNetwork,
    ape.[State] AS CurrentState,
    usa.Abbreviation AS ProposedState,
    ape.PlanID,
    m.PlanFullDescription,
    m.PlanDescription
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
INNER JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND ape.Suffix = m.Suffix
    AND ape.PlanID = m.[Plan]
INNER JOIN [EDI].[Aetna].[AetnaStructure_USStateAbbreviation] usa
    ON m.PlanFullDescription LIKE usa.USStates + ' -%'
WHERE ape.Network = 'Nat' 
  AND ape.[State] IS NULL;







  SELECT 
    ape.ID,
    ape.ControlNumber,
    ape.Suffix,
    ape.Network AS CurrentNetwork,
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        ELSE ape.Network
    END AS ProposedNetwork,
    ape.[State] AS CurrentState,
    usa.Abbreviation AS ProposedState,
    ape.PlanID,
    m.PlanFullDescription,
    m.PlanDescription,
	lookup.Suffix as lookup_suffix,lookup.Network as lookup_Network,
    lookup.[Plan] AS LookupPlanID,
    lookup.PlanDescription AS LookupPlanDescription
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND ape.Suffix = m.Suffix
    AND ape.PlanID = m.[Plan]
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] lookup
    ON ape.PlanID = lookup.[Plan]  -- just checking PlanID existence in master
LEFT JOIN [EDI].[Aetna].[AetnaStructure_USStateAbbreviation] usa
    ON m.PlanFullDescription LIKE usa.USStates + ' -%'
WHERE lookup.Network = 'Nat'
--ORDER BY ape.ID;


select * from controlnumbermapping



select * from [EDI].[Aetna].[AccountStructure_PlanID_Extract]
select * from [Aetna].[lookup_AccountStructure_PlanID] where State is null



SELECT 
    -- ape table
    ape.ID AS ape_ID,
    ape.ControlNumber AS ape_ControlNumber,
    ape.Suffix AS ape_Suffix,
    ape.Network AS ape_Network,
    ape.State AS ape_State,
    ape.IsCoverageBased AS ape_IsCoverageBased,
    ape.CoverageRules AS ape_CoverageRules,
    ape.PlanID AS ape_PlanID,
    ape.ExtractDateTime AS ape_ExtractDateTime,
    ape.DepAge30Flag AS ape_DepAge30Flag,

    -- Proposed network from Master
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        ELSE ape.Network
    END AS ape_ProposedNetwork,

    -- Master table
    m.PlanFullDescription AS master_PlanFullDescription,
    m.PlanDescription AS master_PlanDescription,

    -- USA table
    usa.Abbreviation AS usa_ProposedState,

    -- Lookup table
    lookup.Suffix AS lookup_Suffix,
    lookup.Network AS lookup_Network,
    lookup.PlanID AS lookup_PlanID,
    --lookup.PlanDescription AS lookup_PlanDescription,
    lookup.IsCoverageBased AS lookup_IsCoverageBased,
    lookup.CoverageRules AS lookup_CoverageRules,
    lookup.DepAge30Flag AS lookup_DepAge30Flag,

    -- Control Number Mapping table
    cnm.[PLAN CODE] AS controlmapp_PlanCode,
    cnm.[CoAd Plan Name] AS controlmapp_CoAdPlanName,
    cnm.[Account Name on Coding Supplement] AS controlmapp_Account_Name,
    cnm.[NETWORK FILE] AS controlmapp_Network_File,
    cnm.Control AS controlmapp_Control,
    cnm.SUFFIX AS controlmapp_real_unpadded_in_table_Suffix

FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND ape.Suffix = m.Suffix
    AND ape.PlanID = m.[Plan]
LEFT JOIN [EDI].[Aetna].[lookup_AccountStructure_PlanID] lookup
    ON ape.ControlNumber = lookup.ControlNumber
    AND ape.Suffix = RIGHT('000' + RTRIM(LTRIM(lookup.Suffix)), 3)
LEFT JOIN [EDI].[Aetna].[AetnaStructure_USStateAbbreviation] usa
    ON m.PlanFullDescription LIKE usa.USStates + ' -%'
LEFT JOIN [EDI].[dbo].[controlnumbermapping] cnm
    ON ape.ControlNumber = cnm.Control
    AND ape.Suffix = RIGHT('000' + RTRIM(LTRIM(cnm.SUFFIX)), 3)
WHERE lookup.IsCoverageBased is null and lookup.State is null and lookup.CoverageRules is null or lookup.DepAge30Flag is null



-- Create temporary tables to identify differences
-- First, let's see what records in the lookup table need to be updated
SELECT 
    ape.ControlNumber,
    ape.Suffix,
    ape.Network AS ExtractNetwork,
    ape.State AS ExtractState,
    ape.PlanID AS ExtractPlanID,
    ape.DepAge30Flag,
    lookup.Network AS LookupNetwork,
    lookup.State AS LookupState,
    lookup.PlanID AS LookupPlanID,
    CASE 
        WHEN ape.Network <> lookup.Network OR 
             ape.State <> lookup.State OR 
             ape.PlanID <> lookup.PlanID THEN 'Needs Update'
        ELSE 'Match'
    END AS Status
INTO #PlanIDLookupDifferences
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
INNER JOIN [EDI].[Aetna].[lookup_AccountStructure_PlanID] lookup
    ON ape.ControlNumber = lookup.ControlNumber
    AND ape.Suffix = RIGHT('000' + RTRIM(LTRIM(lookup.Suffix)), 3)
    ---AND ape.DepAge30Flag = lookup.DepAge30Flag
WHERE ape.Network <> lookup.Network 
   OR ape.State <> lookup.State 
   OR ape.PlanID <> lookup.PlanID
   OR lookup.State IS NULL
   OR lookup.PlanID IS NULL
   or ape.DepAge30Flag <> lookup.DepAge30Flag

-- Check how many records need updating
SELECT 'PlanID Lookup Records Needing Update' AS Status, COUNT(*) AS RecordCount
FROM #PlanIDLookupDifferences
WHERE Status = 'Needs Update'

-- Show sample of differences
SELECT TOP 10 * FROM #PlanIDLookupDifferences
WHERE Status = 'Needs Update'



-- Create temp table for cleaned PlanID data
DROP TABLE IF EXISTS #Temp_AccountStructure_PlanID_Extract;
SELECT *
INTO #Temp_AccountStructure_PlanID_Extract
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract];

-- Create temp table for cleaned lookup data
DROP TABLE IF EXISTS #Temp_lookup_AccountStructure_PlanID;
SELECT *
INTO #Temp_lookup_AccountStructure_PlanID
FROM [EDI].[Aetna].[lookup_AccountStructure_PlanID];



-- Update Network and State in temp table
UPDATE tmp
SET 
    tmp.[State] = usa.Abbreviation,
    tmp.Network = CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        ELSE tmp.Network
    END
FROM #Temp_AccountStructure_PlanID_Extract tmp
INNER JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON tmp.ControlNumber = m.ControlNumber
    AND RIGHT('000' + RTRIM(LTRIM(tmp.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(m.Suffix)), 3)
    AND tmp.PlanID = m.[Plan]
INNER JOIN [EDI].[Aetna].[AetnaStructure_USStateAbbreviation] usa
    ON m.PlanFullDescription LIKE usa.USStates + ' -%'
WHERE tmp.Network = 'Nat' 
  AND tmp.[State] IS NULL;



  -- Ensure Suffix is 3-digit in temp table
--UPDATE #Temp_AccountStructure_PlanID_Extract
--SET Suffix = RIGHT('000' + RTRIM(LTRIM(Suffix)), 3)
--WHERE LEN(RTRIM(LTRIM(Suffix))) < 3;


-- Check that bad rows are fixed
SELECT 
    tmp.ID,
    tmp.ControlNumber,
    tmp.Suffix,
    tmp.Network,
    tmp.[State],
    tmp.PlanID,
    m.PlanFullDescription
FROM #Temp_AccountStructure_PlanID_Extract tmp
INNER JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON tmp.ControlNumber = m.ControlNumber
    AND tmp.Suffix = m.Suffix
    AND tmp.PlanID = m.[Plan]
WHERE tmp.Network = 'Nat' OR tmp.[State] IS NULL;

---- Update real lookup table from temp table
--UPDATE lookup
--SET 
--    lookup.Network = tmp.Network,
--    lookup.[State] = tmp.[State],
--    lookup.IsCoverageBased = tmp.IsCoverageBased,
--    lookup.CoverageRules = tmp.CoverageRules,
--    lookup.DepAge30Flag = tmp.DepAge30Flag
--FROM [EDI].[Aetna].[lookup_AccountStructure_PlanID] lookup
--INNER JOIN #Temp_AccountStructure_PlanID_Extract tmp
--    ON lookup.ControlNumber = tmp.ControlNumber
--    AND lookup.Suffix = tmp.Suffix
--    AND lookup.PlanId = tmp.PlanID;

select * from #Temp_lookup_AccountStructure_PlanID where  Network = 'Nat' or State is null

-- Should return 0 rows
select * from [EDI].[Aetna].[lookup_AccountStructure_PlanID] where  Network = 'Nat' or State is null

select * from #Temp_lookup_AccountStructure_PlanID where  Network = 'Nat' or State is null

-- Should return 0 rows

SELECT *
FROM #Temp_AccountStructure_PlanID_Extract
ORDER BY ControlNumber, Suffix;

-- Get all distinct PlanDescription values to validate mapping
SELECT 
    -- Columns from AccountStructure_PlanID_Extract with alias ape_
    ape.ID,
    ape.ControlNumber AS ape_ControlNumber,
    ape.Suffix AS ape_Suffix,
    ape.Network AS ape_Network,
    ape.[State] AS ape_State,
    ape.IsCoverageBased AS ape_IsCoverageBased,
    ape.CoverageRules AS ape_CoverageRules,
    ape.PlanID AS ape_PlanID,
    ape.DepAge30Flag AS ape_DepAge30Flag,

    -- Columns from AetnaStructure_Master with alias master_
    m.InsuranceLineCode AS master_InsuranceLineCode,
    m.ELR AS master_ELR,
    m.ControlNumber AS master_ControlNumber,
    m.Suffix AS master_Suffix,
    m.Account AS master_Account,
    m.[Plan] AS master_Plan,
    m.ClaimOffice AS master_ClaimOffice,
    m.CoverageLevelCode AS master_CoverageLevelCode,
    m.AccountName AS master_AccountName,
    m.PlanFullDescription AS master_PlanFullDescription,
    m.State AS master_State,
    m.PlanDescription AS master_PlanDescription,
    m.Network AS master_Network,
    m.RateBand AS master_RateBand,
    m.ActiveCobraFlag AS master_ActiveCobraFlag,
    m.DepAge30Flag AS master_DepAge30Flag,

    -- Columns from controlnumbermapping with alias cnm_
    cnm.[PLAN CODE] AS cnm_PlanCode,
    cnm.[CoAd Plan Name] AS cnm_CoAdPlanName,
    cnm.[Account Name on Coding Supplement] AS cnm_AccountName,
    cnm.Control AS cnm_Control,
    cnm.SUFFIX AS cnm_Suffix,
    cnm.[NETWORK FILE] AS cnm_NetworkFile,

    -- Mapping logic
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%QPIC%' THEN 'QPIC'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'DALLAS'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'AUSTIN'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'HOUSTON'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'SANANN'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TX'
        WHEN m.PlanDescription LIKE '%COLORADO%' THEN 'CO'
        WHEN m.PlanDescription LIKE '%UTAH%' THEN 'UT'
        WHEN m.PlanDescription LIKE '%S%CAL%' THEN 'SCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' THEN 'NCA'
        ELSE 'UNMAPPED'
    END AS MappedNetwork

FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(m.Suffix)), 3)
    AND ape.PlanID = m.[Plan]
LEFT JOIN [EDI].[dbo].[controlnumbermapping] cnm
    ON ape.ControlNumber = cnm.Control
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(cnm.SUFFIX)), 3)

WHERE
    -- Only unmapped records
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%QPIC%' THEN 'QPIC'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'DALLAS'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'AUSTIN'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'HOUSTON'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'SANANN'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TX'
        WHEN m.PlanDescription LIKE '%COLORADO%' THEN 'CO'
        WHEN m.PlanDescription LIKE '%UTAH%' THEN 'UT'
        WHEN m.PlanDescription LIKE '%S%CAL%' THEN 'SCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' THEN 'NCA'
        ELSE 'UNMAPPED'
    END = 'UNMAPPED';



	-- Check for unmapped PlanDescription values
SELECT DISTINCT PlanFullDescription
FROM [EDI].[Aetna].[AetnaStructure_Master]
WHERE PlanDescription NOT LIKE '%EPO%'
  AND PlanDescription NOT LIKE '%MC%'
  AND PlanDescription NOT LIKE '%MANAGED CHOICE%'
  AND PlanDescription NOT LIKE '%PPO%'
  AND PlanDescription NOT LIKE '%HMO%';






	select * from controlnumbermapping
	select * from [EDI].[Aetna].[lookup_AccountStructure_PlanID]

select * from 	[EDI].[Aetna].[AccountStructure_PlanID_Extract]




SELECT 
    ape.*,
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' 
            OR m.PlanDescription LIKE '%MANAGED CHOICE%' 
            OR m.PlanDescription LIKE '%MCPOS%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' 
            OR m.PlanDescription IN ('N', 'S') 
            OR m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'BAPTIST'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%S%CAL%' 
            OR m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' 
            OR m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%AVN%' THEN 
            CASE 
                WHEN m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCAAVN'
                WHEN m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCAAVN'
                ELSE 'HMONCAAVN'
            END
        WHEN m.PlanDescription LIKE '%CMED%' 
            OR m.PlanDescription LIKE '%INDEMNITY%' THEN 'INDEMOOA'
        ELSE 'UNMAPPED'
    END AS MappedNetwork
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(m.Suffix)), 3)
    AND ape.PlanID = m.[Plan];





	SELECT distinct
    m.PlanDescription,
    m.PlanFullDescription,
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' OR m.PlanDescription LIKE '%MCPOS%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' OR m.PlanDescription IN ('N', 'S') THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'BAPTIST'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%S%CAL%' OR m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' OR m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%AVN%' THEN 
            CASE 
                WHEN m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCAAVN'
                WHEN m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCAAVN'
                ELSE 'HMONCAAVN'
            END
        WHEN m.PlanDescription LIKE '%CMED%' OR m.PlanDescription LIKE '%INDEMNITY%' THEN 'INDEMOOA'
        ELSE 'UNMAPPED'
    END AS MappedNetwork
FROM [EDI].[Aetna].[AetnaStructure_Master] m
WHERE m.PlanDescription IN ('N', 'S', 'ACO Seton HNOnly 2500/70%', 'CMED 1000/80%')
   OR m.PlanFullDescription LIKE '%CALIFORNIA%AVN%'
   OR m.PlanFullDescription LIKE '%CALIFORNIA%HMO%';



   SELECT *
FROM (
    SELECT 
        ape.*,
        CASE 
            WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
            WHEN m.PlanDescription LIKE '%MC%' 
                OR m.PlanDescription LIKE '%MANAGED CHOICE%' 
                OR m.PlanDescription LIKE '%MCPOS%' THEN 'NATLMCPOS'
            WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
            WHEN m.PlanDescription LIKE '%HMO%' 
                OR m.PlanDescription IN ('N', 'S') 
                OR m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
            WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
            WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
            WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
            WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'TXHEALTH'
            WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'SETON'
            WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'MHERMAN'
            WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'BAPTIST'
            WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TXHEALTH'
            WHEN m.PlanDescription LIKE '%S%CAL%' 
                OR m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCA'
            WHEN m.PlanDescription LIKE '%N%CAL%' 
                OR m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCA'
            WHEN m.PlanDescription LIKE '%AVN%' THEN 
                CASE 
                    WHEN m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCAAVN'
                    WHEN m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCAAVN'
                    ELSE 'HMONCAAVN'
                END
            WHEN m.PlanDescription LIKE '%CMED%' 
                OR m.PlanDescription LIKE '%INDEMNITY%' THEN 'INDEMOOA'
            ELSE 'UNMAPPED'
        END AS MappedNetwork
    FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
    LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
        ON ape.ControlNumber = m.ControlNumber
        AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(m.Suffix)), 3)
        AND ape.PlanID = m.[Plan]
) AS sub
WHERE MappedNetwork = 'UNMAPPED';






SELECT 
    ape.ID AS ape_ID,
    ape.ControlNumber AS ape_ControlNumber,
    RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) AS ape_Suffix,
    ape.Network AS ape_Network,
    ape.State AS ape_State,
    ape.IsCoverageBased AS ape_IsCoverageBased,
    ape.CoverageRules AS ape_CoverageRules,
    ape.PlanID AS ape_PlanID,
    ape.DepAge30Flag AS ape_DepAge30Flag,
    
    m.InsuranceLineCode AS master_InsuranceLineCode,
    m.ELR AS master_ELR,
    m.ControlNumber AS master_ControlNumber,
    RIGHT('000' + RTRIM(LTRIM(m.Suffix)), 3) AS master_Suffix,
    m.Account AS master_Account,
    m.[Plan] AS master_Plan,
    m.ClaimOffice AS master_ClaimOffice,
    m.CoverageLevelCode AS master_CoverageLevelCode,
    m.AccountName AS master_AccountName,
    m.PlanFullDescription AS master_PlanFullDescription,
    m.State AS master_State,
    m.PlanDescription AS master_PlanDescription,
    m.Network AS master_Network,
    m.RateBand AS master_RateBand,
    m.ActiveCobraFlag AS master_ActiveCobraFlag,
    m.DepAge30Flag AS master_DepAge30Flag,
    
    cnm.[PLAN CODE] AS cnm_PlanCode,
    cnm.[CoAd Plan Name] AS cnm_CoAdPlanName,
    cnm.[Account Name on Coding Supplement] AS cnm_AccountName,
    cnm.Control AS cnm_Control,
    RIGHT('000' + RTRIM(LTRIM(cnm.SUFFIX)), 3) AS cnm_Suffix,
    cnm.[NETWORK FILE] AS cnm_NetworkFile,
    
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' 
            OR m.PlanDescription LIKE '%MANAGED CHOICE%' 
            OR m.PlanDescription LIKE '%MCPOS%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' 
            OR m.PlanDescription IN ('N', 'S') 
            OR m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'BAPTIST'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%S%CAL%' 
            OR m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' 
            OR m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%AVN%' THEN 
            CASE 
                WHEN m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCAAVN'
                WHEN m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCAAVN'
                ELSE 'HMONCAAVN'
            END
        WHEN m.PlanDescription LIKE '%CMED%' 
            OR m.PlanDescription LIKE '%INDEMNITY%' THEN 'INDEMOOA'
        ELSE 'UNMAPPED'
    END AS MappedNetwork

FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(m.Suffix)), 3)
    AND ape.PlanID = m.[Plan]
LEFT JOIN [EDI].[dbo].[controlnumbermapping] cnm
    ON ape.ControlNumber = cnm.Control
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(cnm.SUFFIX)), 3)
WHERE 
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' 
            OR m.PlanDescription LIKE '%MANAGED CHOICE%' 
            OR m.PlanDescription LIKE '%MCPOS%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' 
            OR m.PlanDescription IN ('N', 'S') 
            OR m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'BAPTIST'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%S%CAL%' 
            OR m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' 
            OR m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%AVN%' THEN 
            CASE 
                WHEN m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCAAVN'
                WHEN m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCAAVN'
                ELSE 'HMONCAAVN'
            END
        WHEN m.PlanDescription LIKE '%CMED%' 
            OR m.PlanDescription LIKE '%INDEMNITY%' THEN 'INDEMOOA'
        ELSE 'UNMAPPED'
    END = 'UNMAPPED';




	SELECT TOP 15
    ape.ControlNumber,
    RIGHT('000' + RTRIM(LTRIM(ape.Suffix)),3) AS Suffix,
    ape.Network,
    m.PlanDescription,
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' 
            OR m.PlanDescription LIKE '%MANAGED CHOICE%' 
            OR m.PlanDescription LIKE '%MCPOS%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'BAPTIST'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%S%CAL%' THEN 'HMOSCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%AVN%' THEN 'AVN'
        WHEN m.PlanDescription LIKE '%CMED%' 
            OR m.PlanDescription LIKE '%INDEMNITY%' THEN 'INDEMOOA'
        ELSE 'UNMAPPED'
    END AS MappedNetwork
FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)),3) = RIGHT('000' + RTRIM(LTRIM(m.Suffix)),3)
    AND ape.PlanID = m.[Plan];






	SELECT distinct
    ape.ControlNumber AS ape_ControlNumber,
    RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) AS ape_Suffix,
    ape.Network AS ape_Network,
    ape.State AS ape_State,
    ape.IsCoverageBased AS ape_IsCoverageBased,
    ape.CoverageRules AS ape_CoverageRules,
    ape.PlanID AS ape_PlanID,
    ape.DepAge30Flag AS ape_DepAge30Flag,

    m.InsuranceLineCode AS master_InsuranceLineCode,
    m.ELR AS master_ELR,
    m.ControlNumber AS master_ControlNumber,
    m.Suffix AS master_Suffix,
    m.Account AS master_Account,
    m.[Plan] AS master_PlanID,
    m.ClaimOffice AS master_ClaimOffice,
    m.CoverageLevelCode AS master_CoverageLevelCode,
    m.AccountName AS master_AccountName,
    m.PlanFullDescription AS master_PlanFullDescription,
    m.State AS master_State,
    m.PlanDescription AS master_PlanDescription,
    m.Network AS master_Network,
    m.RateBand AS master_RateBand,
    m.ActiveCobraFlag AS master_ActiveCobraFlag,
    m.DepAge30Flag AS master_DepAge30Flag,

    cnm.[PLAN CODE] AS cnm_PlanCode,
    cnm.[CoAd Plan Name] AS cnm_CoAdPlanName,
    cnm.[Account Name on Coding Supplement] AS cnm_AccountName,
    cnm.Control AS cnm_Control,
    RIGHT('000' + RTRIM(LTRIM(cnm.SUFFIX)), 3) AS cnm_Suffix,
    cnm.[NETWORK FILE] AS cnm_NetworkFile,

    -- Mapped Network
    CASE 
        WHEN m.PlanDescription LIKE '%EPO%' THEN 'NATLEPO'
        WHEN m.PlanDescription LIKE '%MC%' OR m.PlanDescription LIKE '%MANAGED CHOICE%' OR m.PlanDescription LIKE '%MCPOS%' THEN 'NATLMCPOS'
        WHEN m.PlanDescription LIKE '%PPO%' THEN 'OOAPPO'
        WHEN m.PlanDescription LIKE '%HMO%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%SETON%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%BAYLOR%' THEN 'BAYLOR'
        WHEN m.PlanDescription LIKE '%MHERMAN%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%DALLAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%AUSTIN%' THEN 'SETON'
        WHEN m.PlanDescription LIKE '%HOUSTON%' THEN 'MHERMAN'
        WHEN m.PlanDescription LIKE '%SAN ANTONIO%' THEN 'BAPTIST'
        WHEN m.PlanDescription LIKE '%TEXAS%' THEN 'TXHEALTH'
        WHEN m.PlanDescription LIKE '%S%CAL%' OR m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCA'
        WHEN m.PlanDescription LIKE '%N%CAL%' OR m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCA'
        WHEN m.PlanDescription LIKE '%AVN%' THEN 
            CASE 
                WHEN m.PlanFullDescription LIKE '%S. CAL%' THEN 'HMOSCAAVN'
                WHEN m.PlanFullDescription LIKE '%N. CAL%' THEN 'HMONCAAVN'
                ELSE 'HMONCAAVN'
            END
        WHEN m.PlanDescription LIKE '%CMED%' OR m.PlanDescription LIKE '%INDEMNITY%' THEN 'INDEMOOA'
        ELSE 'UNMAPPED'
    END AS MappedNetwork

FROM [EDI].[Aetna].[AccountStructure_PlanID_Extract] ape
LEFT JOIN [EDI].[Aetna].[AetnaStructure_Master] m
    ON ape.ControlNumber = m.ControlNumber
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(m.Suffix)), 3)
    AND ape.PlanID = m.[Plan]
LEFT JOIN [EDI].[dbo].[controlnumbermapping] cnm
    ON ape.ControlNumber = cnm.Control
    AND RIGHT('000' + RTRIM(LTRIM(ape.Suffix)), 3) = RIGHT('000' + RTRIM(LTRIM(cnm.SUFFIX)), 3)
WHERE 
    -- Only show tricky or unmapped-like cases
    m.PlanDescription LIKE '%N%CAL%'
    OR ape.Network LIKE '%NOMA%'
    OR ape.Network LIKE '%OOA%';
