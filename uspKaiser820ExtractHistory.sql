USE [EDI]

CREATE PROCEDURE [dbo].[uspKaiser820ExtractHistory]

***********************************************************************/
AS
BEGIN
	SET NOCOUNT ON;
	SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

	/********************************************
		Filter only necessary records
	*********************************************/
	SET @FileMonth= CASE WHEN @filemonth='0'

				THEN CONVERT(varchar, GETDATE() +1, 101)
				ELSE @FileMonth 
				END
	DECLARE
		@Carrier VARCHAR(20) = 'Kaiser820',
		@IsActiveFlag INT = 1,
		@CurrentPlanYear INT,
		@EOMONTH DATE=EOMONTH(@FileMonth),
		@BOMONTH DATE=DATEADD(DAY,1,EOMONTH(@FileMonth,-1)),
		@EOMONTHNODASH VARCHAR(8)=REPLACE(EOMONTH(@FileMonth),'-',''),
		@BOMONTHNODASH VARCHAR(8)=REPLACE(DATEADD(DAY,1,EOMONTH(@FileMonth,-1)),'-',''),
		@TransactionSet INT=0

	SELECT
		@CurrentPlanYear = fq.PlanYear

	FROM

	(
		SELECT
			ty.N AS PlanYear,
			CAST(CONCAT((ty.N - 1), '-10-01') AS DATE) AS PlanYearStart,
			CAST(CONCAT(ty.N, '-09-30') AS DATE) AS PlanYearStop
		FROM EDI.dbo.Tally AS ty
		WHERE
			ty.N BETWEEN YEAR(CURRENT_TIMESTAMP) - 1 AND YEAR(CURRENT_TIMESTAMP) + 1

	) AS fq

	WHERE
		CURRENT_TIMESTAMP BETWEEN fq.PlanYearStart AND fq.PlanYearStop

	DROP TABLE IF EXISTS #ActiveRows;

	CREATE TABLE #ActiveRows
	(
		EmployeeBenefitEnrollmentHistoryID INT,
		PayrollSystemClientID VARCHAR(20),
		PayrollSystemEEID VARCHAR(20),
		SubscriberSSN VARCHAR(20),
		BenefitPlanID VARCHAR(20),
		BenefitCoverageEffectiveDate DATETIME
		PRIMARY KEY CLUSTERED ([EmployeeBenefitEnrollmentHistoryID] ASC)
	);

	/******************************************
		Populate Temp Table
	*******************************************/

	----INSERT Active records in Temp Table

	INSERT INTO #ActiveRows
	(
		EmployeeBenefitEnrollmentHistoryID,
		PayrollSystemClientID,
		PayrollSystemEEID,
		SubscriberSSN,
		BenefitPlanID,
		BenefitCoverageEffectiveDate
	)
	SELECT
		ad.EmployeeBenefitEnrollmentHistoryID,
		ad.PayrollSystemClientID,
		ad.PayrollSystemEEID,
		ad.SubscriberSSN,
		ad.BenefitPlanID,
		ad.BenefitCoverageEffectiveDate
	FROM
	(
		SELECT
			bei.EmployeeBenefitEnrollmentHistoryID,
			bei.PayrollSystemClientID,
			bei.PayrollSystemEEID,
			bei.SubscriberSSN,
			bei.BenefitPlanID,
			bei.BenefitCoverageEffectiveDate,
			DENSE_RANK() OVER
			(
				PARTITION BY
					bei.PayrollSystemClientID,
					bei.PayrollSystemEEID,
					bei.InsuredID
				ORDER BY
					bei.BenefitCoverageEffectiveDate DESC
			) AS RwNo

		FROM EDI.dbo.vwEmployeeBenefitEnrollmentHistory AS bei WITH(NOLOCK)
		WHERE
			bei.BenefitPlanYear <= @CurrentPlanYear
			AND bei.BenefitCoverageEffectiveDate<=@EOMONTH
			AND (bei.BenefitStatusCode='A') 
			AND bei.BenefitPlanID LIKE 'CMK%'
			AND bei.SubscriberDependentFlag='S'
		) AS ad

	WHERE
		ad.RwNo = 1
	--
	-- Terms And cobra terms(for current month)
	--
	BEGIN
		INSERT INTO #ActiveRows
		(
			EmployeeBenefitEnrollmentHistoryID,
			PayrollSystemClientID,
			PayrollSystemEEID,
			SubscriberSSN,
			BenefitPlanID,
			BenefitCoverageEffectiveDate
		)
		SELECT
			ad.EmployeeBenefitEnrollmentHistoryID,
			ad.PayrollSystemClientID,
			ad.PayrollSystemEEID,
			ad.SubscriberSSN,
			ad.BenefitPlanID,
			ad.BenefitCoverageEffectiveDate
		FROM
		(
			SELECT
				bei.EmployeeBenefitEnrollmentHistoryID,
				bei.PayrollSystemClientID,
				bei.PayrollSystemEEID,
				bei.SubscriberSSN,
				bei.BenefitPlanID,
				bei.BenefitCoverageEffectiveDate,
				DENSE_RANK() OVER
				(
					PARTITION BY
						bei.PayrollSystemClientID,
						bei.PayrollSystemEEID,
						bei.InsuredID
					ORDER BY
						bei.BenefitCoverageEffectiveDate DESC
				) AS RwNo
			FROM EDI.dbo.vwEmployeeBenefitEnrollmentHistory AS bei WITH(NOLOCK)
			WHERE
				bei.BenefitPlanID LIKE 'CMK%'
				AND bei.BenefitCoverageEffectiveDate<=@EOMONTH
				AND bei.SubscriberDependentFlag='S'
				AND bei.BenefitStatusCode = 'T' 
				AND bei.BenefitCoverageEndDate BETWEEN @BOMONTH AND @EOMONTH
				AND bei.BenefitCoverageEffectiveDate<>ISNULL(bei.BenefitCoverageEndDate,'12/31/9999')
				AND bei.BenefitPlanYear <= @CurrentPlanYear
				AND NOT EXISTS
				(
					(
						SELECT
							ar.EmployeeBenefitEnrollmentHistoryID
						FROM #ActiveRows ar
						WHERE
							ar.PayrollSystemClientID = bei.PayrollSystemClientID
							AND ar.PayrollSystemEEID = bei.PayrollSystemEEID
					)
					UNION
					(
						SELECT
							ar.EmployeeBenefitEnrollmentHistoryID
						FROM #ActiveRows ar
						WHERE
							ar.SubscriberSSN = bei.SubscriberSSN
					)
				)
		) AS ad
		WHERE
			ad.RwNo = 1
	END

	--TFS# for including past terms and future terms

	BEGIN
		INSERT INTO #ActiveRows
		(
			EmployeeBenefitEnrollmentHistoryID,
			PayrollSystemClientID,
			PayrollSystemEEID,
			SubscriberSSN,
			BenefitPlanID,
			BenefitCoverageEffectiveDate
		)
		SELECT
			ad.EmployeeBenefitEnrollmentHistoryID,
			ad.PayrollSystemClientID,
			ad.PayrollSystemEEID,
			ad.SubscriberSSN,
			ad.BenefitPlanID,
			ad.BenefitCoverageEffectiveDate
		FROM
		(
			SELECT
				bei.EmployeeBenefitEnrollmentHistoryID,
				bei.PayrollSystemClientID,
				bei.PayrollSystemEEID,
				bei.SubscriberSSN,
				bei.BenefitPlanID,
				bei.BenefitCoverageEffectiveDate,
				DENSE_RANK() OVER
				(
					PARTITION BY
						bei.PayrollSystemClientID,
						bei.PayrollSystemEEID,
						bei.InsuredID
					ORDER BY
						bei.BenefitCoverageEffectiveDate DESC
				) AS RwNo
			FROM EDI.dbo.vwEmployeeBenefitEnrollmentHistory AS bei WITH(NOLOCK)
			WHERE
				bei.BenefitPlanID LIKE 'CMK%'
				AND bei.BenefitCoverageEffectiveDate<=@EOMONTH
				AND bei.SubscriberDependentFlag='S'
				AND bei.BenefitStatusCode = 'T' 
				--AND bei.BenefitCoverageEndDate BETWEEN @BOMONTH AND @EOMONTH
				--AND bei.BenefitCoverageEndDate > @eomonth
					and 	1 = (case 
            when bei.BenefitCoverageEndDate > = @EOMonth then 1

             when bei.BenefitCoverageEndDate > = @BOMonth then 1

             else 0
         end)
				AND bei.BenefitCoverageEffectiveDate<>ISNULL(bei.BenefitCoverageEndDate,'12/31/9999')
				AND bei.BenefitPlanYear = @CurrentPlanYear
				AND NOT EXISTS
				(
					(
						SELECT
							ar.EmployeeBenefitEnrollmentHistoryID
						FROM #ActiveRows ar
						WHERE
							ar.PayrollSystemClientID = bei.PayrollSystemClientID
							AND ar.PayrollSystemEEID = bei.PayrollSystemEEID
					)
					UNION
					(
						SELECT
							ar.EmployeeBenefitEnrollmentHistoryID
						FROM #ActiveRows ar
						WHERE
							ar.SubscriberSSN = bei.SubscriberSSN
					)
				)
		) AS ad
		WHERE
			ad.RwNo = 1
	END
	
	/*************************************************
		Generate all the necessary variables
	**************************************************/

	DECLARE @Timestamp VARCHAR(12)
	SET @TimeStamp =  REPLACE(CONVERT(VARCHAR(12), GETDATE(), 114), ':','')
	SET @TimeStamp =
	(
		CASE
			WHEN LEFT(@Timestamp, 1) = '0' THEN STUFF(@Timestamp, 1, 1, '')
			ELSE @Timestamp
		END
	)

	DECLARE @TimeFormat VARCHAR(10)
	SET @TimeFormat = CONVERT(VARCHAR(8),GETDATE(),112)
	DECLARE @InterchangeControlNumber VARCHAR(9)
	SET @InterchangeControlNumber=  RIGHT(EDI.dbo.ToFileTime(CURRENT_TIMESTAMP),9)


	DROP TABLE IF EXISTS #vwEmployeeBenefitEnrollmentHistory;
	SELECT DISTINCT
	bei.SubscriberSSN AS SubscriberSSN,
	CONCAT(

	a.GroupNumber, ISNULL(RIGHT(REPLICATE('0',4) + A.RefDXValue, 4),'0000'))	--REF02 - Reference Identification

	AS [Policy_Number],
	bei.SubscriberLastName,
	bei.SubscriberFirstName,
	bei.SubscriberMiddleName,
	bei.SubscriberSuffix,

	(CASE 
		WHEN bei.PayrollsystemClientID  IN ('481001','531001') THEN (bei.SubscriberTotalContribution+bei.EmployerTotalContribution) 
		WHEN kf.Amount IS NULL THEN (bei.SubscriberTotalContribution+bei.EmployerTotalContribution) 
		ELSE CAST(((bei.SubscriberTotalContribution+bei.EmployerTotalContribution) -kf.amount) AS decimal(18,2))
	END) AS [TotalContribution],

	CONCAT(@BOMONTHNODASH,'-',@EOMONTHNODASH) as [CoveragePeriod],
	0 as SECount,
	0 as BPRTotal
	INTO #vwEmployeeBenefitEnrollmentHistory
	FROM EDI.dbo.vwEmployeeBenefitEnrollmentHistory AS bei WITH (NOLOCK)
	INNER JOIN #ActiveRows AS ar
		ON bei.EmployeeBenefitEnrollmentHistoryID = ar.EmployeeBenefitEnrollmentHistoryID
	LEFT OUTER JOIN EDI.dbo.Kaiser834_Interpretation AS A
		   ON bei.benefitplanid = A.BenefitPlanID
			AND bei.BenefitStatusCode = A.BenefitStatusCode
			AND bei.BenefitRateBand = A.BenefitRateTier
	LEFT JOIN [EDI].[dbo].[kaiserFee] kf
			ON  1 = (CASE WHEN kf.PreTaxDeductionPlan=bei.BenefitPlanID THEN 1
						WHEN kf.PostTaxDeductionPlan=bei.BenefitPlanID THEN 1
						ELSE 0
					END)
				AND CAST( kf.RateBand AS varchar)=cast(bei.BenefitRateBand as varchar)
				AND kf.AmountType=bei.BenefitCoverageTier
	UNION ALL
	SELECT
	  sq.SubscriberSSN,
	  sq.Policy_Number,
	  sq.SubscriberLastName,
	  sq.SubsciberFirstName,
	  sq.SubscriberMiddleName,
	  sq.SubscriberSuffix,
	  sq.TotalContribution,
	  sq.CoveragePeriod,
	  sq.SECount,
	  sq.BPRTotal
	FROM (SELECT DISTINCT
	  ka.[SubscriberSSN],
	  CONCAT(ISNULL(RIGHT(REPLICATE('0', 9) + CAST(ka.[PID] AS varchar(9)), 9), '000000000'), ISNULL(RIGHT(REPLICATE('0', 4) + ka.[EU], 4), '0000'))
	  AS Policy_Number,
	  v.SubscriberLastName AS SubscriberLastName,
	  v.SubscriberFirstName AS SubsciberFirstName,
	  v.SubscriberMiddleName AS SubscriberMiddleName,
	  v.SubscriberSuffix AS SubscriberSuffix,
	  ka.Membersdue AS TotalContribution,
	  CONCAT(REPLACE(DATEADD(DAY, 1, EOMONTH(ka.[CoveragePeriod], -1)), '-', ''),
	  '-', REPLACE(EOMONTH(ka.[CoveragePeriod]), '-', '')) AS [CoveragePeriod],
	  0 AS SECount,
	  0 AS BPRTotal,
	  ROW_NUMBER() OVER (PARTITION BY ka.[SubscriberSSN],  CONCAT(REPLACE(DATEADD(DAY, 1, EOMONTH(ka.[CoveragePeriod], -1)), '-', ''),
	  '-', REPLACE(EOMONTH(ka.[CoveragePeriod]), '-', '')) ,v.SubscriberLastName, ka.Membersdue  ORDER BY v.SubscriberLastName, v.SubscriberMiddleName DESC) AS RowNumber
	FROM EDI.dbo.Kaiser_820_Adjustments ka
	INNER JOIN EDI.dbo.vwEmployeeBenefitEnrollmentHistory v
	  ON ka.[SubscriberSSN] = v.SubscriberSSN
	WHERE v.BenefitCoverageEffectiveDate >= '10/1/2021' and month(InsertedOn)=MONTH(@FileMonth) and YEAR(InsertedOn)=YEAR(@FileMonth)
	) sq
	WHERE sq.RowNumber = 1

--This update make sure unique name per SSN

	UPDATE v
	SET v.SubscriberFirstName=sq.SubscriberFirstName
	,v.SubscriberLastName=sq.SubscriberLastName
	,v.SubscriberMiddleName=sq.SubscriberMiddleName
	,v.SubscriberSuffix=sq.SubscriberSuffix
	FROM #vwEmployeeBenefitEnrollmentHistory v
	INNER JOIN (SELECT iv.*,ROW_NUMBER() OVER (PARTITION BY iv.[SubscriberSSN],iv.SubscriberLastName 
	ORDER BY iv.SubscriberLastName, iv.SubscriberMiddleName DESC) AS RowNumber
	FROM #vwEmployeeBenefitEnrollmentHistory iv ) sq
	ON sq.subscriberssn=v.subscriberssn
	and sq.RowNumber=1


	DROP TABLE IF EXISTS #BPRTotal
	SELECT DISTINCT SubscriberSSN, Policy_Number,
	SUM(TotalContribution) as BPRTotal
	INTO #BPRTotal
	FROM #vwEmployeeBenefitEnrollmentHistory 
	GROUP BY SubscriberSSN,Policy_Number

	UPDATE 
		 t1
	SET 
		 t1.BPRTotal=t2.BPRTotal
	FROM 
		#vwEmployeeBenefitEnrollmentHistory t1
		INNER JOIN #BPRTotal t2 ON t2.SubscriberSSN=t1.SubscriberSSN
		AND t1.Policy_Number=t2.Policy_Number

	DROP TABLE IF EXISTS #SECount
	SELECT DISTINCT SubscriberSSN, Policy_Number,
	Count(*) AS SECount
	INTO #SECount
	FROM #vwEmployeeBenefitEnrollmentHistory 
	GROUP BY SubscriberSSN,Policy_Number

	UPDATE 
		 t1
	SET 
		 t1.SECount=t2.SECount
	FROM 
		#vwEmployeeBenefitEnrollmentHistory t1
		INNER JOIN #SECount t2 ON t2.SubscriberSSN=t1.SubscriberSSN
		AND t1.Policy_Number=t2.Policy_Number
	

	/**************************************************************
		Populate EDI.dbo.Data820_Kaiser table
	***************************************************************/

DECLARE @Data820Rows TABLE
(
RowNumber INT IDENTITY(1,1),
SubscriberSSN VARCHAR(50),
Policy_Number VARCHAR(50),
SubscriberLastName  VARCHAR(50),
SubscriberFirstName  VARCHAR(50),
SubscriberMiddleName  VARCHAR(50),
SubscriberSuffix  VARCHAR(50),
BPRTotal numeric(10,2),
SECount INT
)

INSERT INTO @Data820Rows 

(
SubscriberSSN,
Policy_Number,
SubscriberLastName,
SubscriberFirstName,
SubscriberMiddleName,
SubscriberSuffix,
BPRTotal,
SECount
)

SELECT
v.SubscriberSSN,
v.Policy_Number,
v.SubscriberLastName,
v.SubscriberFirstName,
v.SubscriberMiddleName,
v.SubscriberSuffix,
v.BPRTotal,
v.SECount

FROM

(

SELECT DISTINCT
			RIGHT(REPLICATE('0',9)+REPLACE(ISNULL(SubscriberSSN,''),'-',''),9)	AS SubscriberSSN,
			Policy_Number								AS Policy_Number,
			UPPER(ISNULL(SubscriberLastName,''))					AS SubscriberLastName,
			UPPER(ISNULL(SubscriberFirstName,''))					AS SubscriberFirstName,
			UPPER(ISNULL(SubscriberMiddleName,''))					AS SubscriberMiddleName,
			UPPER(ISNULL(SubscriberSuffix, ''))					AS SubscriberSuffix,
			BPRTotal,
			SECount
FROM #vwEmployeeBenefitEnrollmentHistory) as v

DECLARE @CoverageRows TABLE
(
SubscriberSSN VARCHAR(50),
Policy_Number VARCHAR(50),
CoveragePeriod VARCHAR(50),
TotalContribution numeric(10,2)
)
INSERT INTO @CoverageRows 
(
SubscriberSSN,
Policy_Number,
CoveragePeriod,
TotalContribution
)
SELECT
c.SubscriberSSN,
c.Policy_Number,
c.CoveragePeriod,
c.TotalContribution
FROM

(
SELECT DISTINCT
			RIGHT(REPLICATE('0',9)+REPLACE(ISNULL(SubscriberSSN,''),'-',''),9)	AS SubscriberSSN,
			Policy_Number		AS Policy_Number,
			CoveragePeriod		AS CoveragePeriod,
			TotalContribution	AS TotalContribution

FROM #vwEmployeeBenefitEnrollmentHistory) as c

DROP TABLE IF EXISTS #Temp



	/***********************************************************************************
								Header Segment Begins
	************************************************************************************/
	DECLARE @Header TABLE
	(
		RowNumber INT IDENTITY(1,1),
		DataRows VARCHAR(MAX)
	)

	DECLARE @Body TABLE
	(
		RowNumber INT IDENTITY(1,1),
		DataRows VARCHAR(MAX)
	)



	INSERT @Header(DataRows)
	--
	--ISA Header
	--
	SELECT
		'ISA' + '*' +
		'00' + '*'							--ISA01 - Authorization Informaton Qualifier
		+'          '+ '*'					--ISA02 - Authorization Information
		+'00' +'*'							--ISA03 - Security Information Qualifier
		+'          ' + '*'					--ISA04 - Security Information
		+'30' + '*'							--ISA05 - Interchange ID Qualifier
		+'46-1569854     ' + '*'			--ISA06 - Interchange Sender ID
		+'ZZ' + '*'							--ISA07 - Interchange ID Qualifier
		+'076011108LCSP  ' + '*'			--ISA08 - Interchange Receiver ID

		+CONVERT(VARCHAR(6),GETDATE(),12) + '*'	--ISA09 - Interchange Date 

		+FORMAT(GETDATE(),'hhmm') + '*'			--ISA10 - Interchange Time -- the date where the file is generated
		+'^' + '*'								--ISA11 - Repetition Seperator
		+'00501' + '*'							--ISA12 - Interchange Control Version
		+@InterchangeControlNumber+'*'			--ISA13 - Interchange Control Number
		+'0' + '*'								--ISA14 - Acknowledgment Requested
		+'P' + '*'								--ISA15 - Interchange Usage Indicator( T for Test or P for Production)
		+':'									--ISA16 - Component Element Separator
		+'~'

	--
	--Group Header
	--
	UNION ALL
	SELECT
		'GS'+ '*'
		+'RA'+'*'										--GS01 - Functional Identifier Code
		+'46-1569854' +'*'								--GS02 - Application Sender's Code
		+'GCACOADVANTAGRP' +'*'							--GS03 - Application Receiver's Code
		+@TimeFormat + '*'								--GS04 - Date
		+FORMAT(GETDATE(),'hhmm') + '*'			--GS05 - Time -- the date when the file is generated
		+RIGHT(@Timestamp,4)+'*'						--GS06 - Group Control Number
		+'X'+'*'										--GS07 - Responsible Agency Code
		+'005010X218'								    --GS08 - Version/Release/Industry Identifier Code
		+'~'
	
	DROP TABLE IF EXISTS #FinalResult
	CREATE TABLE #FinalResult
	(
		RowNum INT IDENTITY(1,1),
		DataRows VARCHAR(MAX),
		Seq SMALLINT
	)

	INSERT INTO #FinalResult
	(
		DataRows,
		Seq
	)
		SELECT
			DataRows,
			1 AS Seq
		FROM @Header
		ORDER BY
			RowNumber


	/**********************************************
		Enrollment Segment Begins
	***********************************************/
	
	SET @TransactionSet = @TransactionSet+1
	INSERT INTO @Body(DataRows)
	SELECT DataRows
	FROM
	(	
	SELECT
	'ST'+'*'
	+'820'+'*'
	+FORMAT(dt.RowNumber,'0###')+'*'
	+'005010X218'
	+'~' AS DataRows,
	dt.RowNumber AS dtSortOrder,
	1 AS SegmentSortOrder
	FROM @Data820Rows as dt

	UNION ALL

	SELECT		
		'BPR'+'*'																
		+'I'+'*'									--BPR01 - Transaction Handling code 
		+CAST(dt.BPRTotal AS VARCHAR(50))   +'*'					--BPR02 - Monetory Amount(Total amount for the group/div)
		+'C'+'*'									--BPR03 - Credit/Debit Flag code
		+'ACH'+ '******'								--BPR04 - Payment Method Code
		+'1461569854' + '******'							--BPR10 - Originating Company Identifier
		+@TimeFormat 									--BPR16 - Date
		+'~' AS DataRows,
			dt.RowNumber AS dtSortOrder,
			2 AS SegmentSortOrder
			FROM @Data820Rows as dt


	--
	--TRN Segment - Re-association Trace Number
	--
	UNION ALL
	SELECT
		'TRN'+'*'
		+'3'+'*'						--TRN01 - Trace Type Code
		+@TimeFormat+'*'							--TRN02 - Reference Identification
		+'1461569854'									--TRN03 - Originating Company Identifier
		+'~' AS DataRows,
			dt.RowNumber AS dtSortOrder,
			3 AS SegmentSortOrder
			FROM @Data820Rows as dt
	
	--REF Segment - Premium Receivers Identification Key
	

	UNION ALL
	SELECT DISTINCT
		'REF'+'*'
		+'14'+'*'									--REF01 - Reference ID Qualifier
		+Policy_Number										--REF02 - Reference Identification
		+'~' AS DataRows,
			dt.RowNumber AS dtSortOrder,
			4 AS SegmentSortOrder
			FROM @Data820Rows dt

	
	UNION ALL
	SELECT
		'DTM'+'*'
		+'582'+'****'
		+'RD8'+'*'									--DTP01 - Date/Time Qualigfier
		+CONCAT(@BOMONTHNODASH,'-',@EOMONTHNODASH)				--DTP02 - Date Time Period Format Qualifier
		+'~' AS DataRows,
			dt.RowNumber AS dtSortOrder,
			5 AS SegmentSortOrder
			FROM @Data820Rows as dt
	

	--
	--QTY - Dependent Total
	--
	UNION ALL
	SELECT
		'N1'+'*'
		+'PE'+'*'							--QTY01 - Dependent Total Qualifier
		+'Kaiser Permanente'+'*'							--QTY02 - Dependent Total INS*N
		+'FI'+'*'						
		+'94-1340523'
		+'~' AS DataRows,
			dt.RowNumber AS dtSortOrder,
			6 AS SegmentSortOrder
			FROM @Data820Rows as dt
	
	--QTY - Dependent Total
	--
	UNION ALL
	SELECT
		'N1'+'*'
		+'PR'+'*'									--QTY01 - Dependent Total Qualifier
		+'COADVANTAGE'+'*'								--QTY02 - Dependent Total INS*N
		+'FI'+'*'						
		+'46-1569854'
		+'~' AS DataRows,
			dt.RowNumber AS dtSortOrder,
			7 AS SegmentSortOrder
			FROM @Data820Rows as dt

	--
	--ENT - 
	--
	UNION ALL
	SELECT
		'ENT'+'*'
		+CAST(dt.RowNumber AS VARCHAR(50))+'*'		--QTY01 - Employee Total Qualifier
		+'2J'+'*'
		+'34'+'*'
		+dt.SubscriberSSN		--QTY02 - Employee Total INS*Y
		+'~' AS	 DataRows,
			dt.RowNumber AS dtSortOrder,
			8 AS SegmentSortOrder
			FROM @Data820Rows as dt

	--
	--NM1 - Name
	--
	UNION ALL
	SELECT
		'NM1'+'*'
		+'EY'+'*'											--QTY01 - Total Qualifier
		+'1'+'*'
		+LTRIM(RTRIM(dt.SubscriberLastName))+'*'
		+LTRIM(RTRIM(dt.SubscriberFirstName))+'*'
		+LTRIM(RTRIM(dt.SubscriberMiddleName))+'*'
		+LTRIM(RTRIM(dt.SubscriberSuffix))+'**'
		+'34'+'*'
		+dt.SubscriberSSN
		+'~' AS DataRows,
		dt.RowNumber AS SortOrder,
		9 AS SegmentSortOrder
			FROM @Data820Rows as dt

	--
	--RMR Segment
	--
	UNION ALL
	SELECT
		'RMR'+'*'
		+'AZ'+'*'									--N101 - Entity Identifier Code
		+cr.subscriberssn+'**'						--N102 - Plan Sponser Name
		+CAST(cr.TotalContribution AS VARCHAR(50))
		+'~' 
		--
		+'<br>' --
		+'DTM'+'*'
		+'582'+'****'								--N101 - Entity Identification Code
		+'RD8'+'*'									--N102 - Insurer Name
		+cr.CoveragePeriod							--N103 - Identification Code Qualifier
		+'~'AS DataRows,
		dt.RowNumber AS SortOrder,
		11 AS SegmentSortOrder
			FROM @Data820Rows as dt
			INNER JOIN @CoverageRows cr
			ON dt.SubscriberSSN=cr.SubscriberSSN AND dt.Policy_Number =cr.Policy_Number

	UNION ALL
	SELECT
		'SE'+'*'
		+CAST(12+((dt.SECount-1)*2) AS VARCHAR(50))+'*'
		+FORMAT(dt.RowNumber,'0###') --SE02 - Transaction Set Control Number
		+'~' AS DataRows,
		dt.RowNumber AS SortOrder,
		12 AS SegmentSortOrder
		FROM @Data820Rows as dt
	
	) AS sq
		ORDER BY
		sq.dtSortOrder,
		sq.SegmentSortOrder;
	
	DECLARE @MaxCnt INT =(SELECT MAX(ID) FROM EDI.dbo.Data820_Kaiser)+1

	DECLARE @BodyAdj TABLE
	(
		RowNumber INT IDENTITY(1,1),
		DataRows VARCHAR(MAX)
	)


	/***********************************
		Trailer Segments Begins
	************************************/

	INSERT INTO #FinalResult
	(
		DataRows,
		Seq
	)
		SELECT
			REPLACE(DataRows, '<br>', CHAR(13) + CHAR(10)),
			2 AS Seq
		FROM @Body
		ORDER BY
			RowNumber
	DECLARE @Footer TABLE
	(
		RowNumber INT IDENTITY(1,1),
		DataRows VARCHAR(MAX)
	)
	DECLARE @GECount INT = (SELECT COUNT(*) FROM #FinalResult WHERE DataRows LIKE 'ST*820%')
	
	INSERT INTO @Footer(DataRows)


	SELECT
		'GE'+'*'
		+CONVERT(VARCHAR(10),@GECount)+'*'							--GE01 - Number of Transaction Sets Included
		+RIGHT(@Timestamp,4)									--GE02 - Group Control Number(Matches GS06)
		+'~' 

	--
	--IEA Segment
	--
	UNION ALL
	SELECT
		'IEA'+'*'
		+'1'+'*'									--IEA01 - Number of Included Functional Groups
		+@InterchangeControlNumber							--IEA02 - Interchange Control Number
		+'~'

	/************************************************
		Final Result Set 
	************************************************/


	INSERT INTO #FinalResult(DataRows,Seq)
	SELECT DataRows,3 AS Seq FROM @Footer ORDER BY RowNumber


	SELECT DataRows FROM #FinalResult
	ORDER BY Seq, RowNum


	TRUNCATE TABLE [dbo].[Kaiser820FinalContributionDetails]

	INSERT INTO [dbo].[Kaiser820FinalContributionDetails]
	(
	SubscriberSSN,
	SubscriberLastName,
	SubscriberFirstName,
	SubscriberMiddleName,
	TotalContribution,
	CoveragePeriod,
	[Group],
	[Division]
	)
	SELECT dr.SubscriberSSN,dr.SubscriberLastName,dr.SubscriberFirstName,dr.SubscriberMiddleName,
	cr.TotalContribution,cr.CoveragePeriod,LEFT(cr.policy_number,9) AS [Group],
	RIGHT(cr.Policy_Number,4) as [Division]

    	FROM @Data820Rows dr

	INNER JOIN @CoverageRows cr

	ON dr.SubscriberSSN=cr.SubscriberSSN AND dr.Policy_Number=cr.Policy_Number
	
	
	SET NOCOUNT OFF;
END
GO


