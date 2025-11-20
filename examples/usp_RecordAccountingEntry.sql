/*
 * Accounting Entry Recording Procedure
 * Records financial transactions
 */

CREATE PROCEDURE [dbo].[usp_RecordAccountingEntry]
    @TransactionId VARCHAR(50),
    @Amount DECIMAL(18,2),
    @TransactionType VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @AccountingPeriod VARCHAR(10);
    DECLARE @FiscalYear INT;
    
    BEGIN TRY
        -- Determine accounting period
        SET @FiscalYear = YEAR(GETUTCDATE());
        SET @AccountingPeriod = CONVERT(VARCHAR(6), GETUTCDATE(), 112);
        
        -- Record the entry
        INSERT INTO dbo.AccountingEntries (
            TransactionId, TransactionType, Amount,
            FiscalYear, AccountingPeriod, EntryDate
        )
        VALUES (
            @TransactionId, @TransactionType, @Amount,
            @FiscalYear, @AccountingPeriod, GETUTCDATE()
        );
        
        -- Update period totals
        UPDATE dbo.AccountingPeriodSummary
        SET TotalRevenue = TotalRevenue + @Amount,
            TransactionCount = TransactionCount + 1,
            LastUpdatedDate = GETUTCDATE()
        WHERE FiscalYear = @FiscalYear
            AND AccountingPeriod = @AccountingPeriod;
        
        -- Insert if not exists
        IF @@ROWCOUNT = 0
        BEGIN
            INSERT INTO dbo.AccountingPeriodSummary (
                FiscalYear, AccountingPeriod, TotalRevenue,
                TransactionCount, LastUpdatedDate
            )
            VALUES (
                @FiscalYear, @AccountingPeriod, @Amount,
                1, GETUTCDATE()
            );
        END
        
        RETURN 0;
    END TRY
    BEGIN CATCH
        DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMsg, 16, 1);
        RETURN -1;
    END CATCH
END
GO
