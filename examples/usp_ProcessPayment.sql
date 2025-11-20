/*
 * Payment Processing Procedure (Called by usp_ProcessCustomerOrder)
 * Demonstrates procedure dependency detection
 */

CREATE PROCEDURE [dbo].[usp_ProcessPayment]
    @OrderId INT,
    @Amount DECIMAL(18,2),
    @ProcessedBy VARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @PaymentStatus VARCHAR(20);
    DECLARE @TransactionId VARCHAR(50);
    
    BEGIN TRY
        -- Generate transaction ID
        SET @TransactionId = 'TXN' + CAST(@OrderId AS VARCHAR) + '_' + 
                            CONVERT(VARCHAR, GETUTCDATE(), 112) + 
                            REPLACE(CONVERT(VARCHAR, GETUTCDATE(), 108), ':', '');
        
        -- Record payment
        INSERT INTO dbo.Payments (
            OrderId, Amount, TransactionId,
            PaymentStatus, PaymentDate, ProcessedBy
        )
        VALUES (
            @OrderId, @Amount, @TransactionId,
            'Completed', GETUTCDATE(), @ProcessedBy
        );
        
        -- Call accounting integration
        EXEC dbo.usp_RecordAccountingEntry
            @TransactionId = @TransactionId,
            @Amount = @Amount,
            @TransactionType = 'Sale';
        
        RETURN 0;
    END TRY
    BEGIN CATCH
        DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMsg, 16, 1);
        RETURN -1;
    END CATCH
END
GO
