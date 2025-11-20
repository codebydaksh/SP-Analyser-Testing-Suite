/*
 * Customer Tier Update Procedure
 * Manages customer loyalty tiers
 */

CREATE PROCEDURE [dbo].[usp_UpdateCustomerTier]
    @CustomerId INT,
    @NewTier VARCHAR(20)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @CurrentTier VARCHAR(20);
    
    BEGIN TRY
        SELECT @CurrentTier = CustomerTier
        FROM dbo.Customers WITH (UPDLOCK)
        WHERE CustomerId = @CustomerId;
        
        IF @CurrentTier != @NewTier OR @CurrentTier IS NULL
        BEGIN
            UPDATE dbo.Customers
            SET CustomerTier = @NewTier,
                TierUpdatedDate = GETUTCDATE()
            WHERE CustomerId = @CustomerId;
            
            -- Log tier change
            INSERT INTO dbo.CustomerTierHistory (
                CustomerId, OldTier, NewTier, ChangedDate
            )
            VALUES (
                @CustomerId, @CurrentTier, @NewTier, GETUTCDATE()
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
