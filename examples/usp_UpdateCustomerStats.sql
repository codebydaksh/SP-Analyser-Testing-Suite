/*
 * Customer Statistics Update Procedure
 * Updates customer lifetime value and order counts
 */

CREATE PROCEDURE [dbo].[usp_UpdateCustomerStats]
    @CustomerId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @TotalOrders INT;
    DECLARE @LifetimeValue DECIMAL(18,2);
    DECLARE @LastOrderDate DATETIME;
    
    BEGIN TRY
        BEGIN TRANSACTION UpdateStats;
        
        -- Calculate statistics
        SELECT 
            @TotalOrders = COUNT(*),
            @LifetimeValue =SUM(TotalAmount),
            @LastOrderDate = MAX(OrderDate)
        FROM dbo.Orders WITH (NOLOCK)
        WHERE CustomerId = @CustomerId
            AND OrderStatus = 'Completed'
            AND IsDeleted = 0;
        
        -- Update customer record
        UPDATE dbo.Customers
        SET TotalOrderCount = @TotalOrders,
            LifetimeValue = @LifetimeValue,
            LastOrderDate = @LastOrderDate,
            LastUpdatedDate = GETUTCDATE()
        WHERE CustomerId = @CustomerId;
        
        -- Update customer tier if applicable
        IF @LifetimeValue >= 10000
            EXEC dbo.usp_UpdateCustomerTier @CustomerId = @CustomerId, @NewTier = 'Platinum';
        ELSE IF @LifetimeValue >= 5000
            EXEC dbo.usp_UpdateCustomerTier @CustomerId = @CustomerId, @NewTier = 'Gold';
        ELSE IF @LifetimeValue >= 1000
            EXEC dbo.usp_UpdateCustomerTier @CustomerId = @CustomerId, @NewTier = 'Silver';
        
        COMMIT TRANSACTION UpdateStats;
        RETURN 0;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION UpdateStats;
        
        DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMsg, 16, 1);
        RETURN -1;
    END CATCH
END
GO
