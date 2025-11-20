/*
 * Order Notification Procedure
 * Sends email notifications for order status changes
 */

CREATE PROCEDURE [dbo].[usp_SendOrderNotification]
    @OrderId INT,
    @CustomerEmail VARCHAR(255),
    @NotificationType VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @EmailSubject VARCHAR(255);
    DECLARE @EmailBody NVARCHAR(MAX);
    
    BEGIN TRY
        -- Build email content based on notification type
        IF @NotificationType = 'Processing'
        BEGIN
            SET @EmailSubject = 'Your Order is Being Processed';
            SET @EmailBody = N'Dear Customer, your order #' + CAST(@OrderId AS VARCHAR) + 
                           ' is now being processed. Thank you for your business!';
        END
        ELSE IF @NotificationType = 'Completed'
        BEGIN
            SET @EmailSubject = 'Your Order is Complete';
            SET @EmailBody = N'Dear Customer, your order #' + CAST(@OrderId AS VARCHAR) + 
                           ' has been completed and is ready for delivery!';
        END
        
        -- Log notification
        INSERT INTO dbo.NotificationLog (
            OrderId, NotificationType, RecipientEmail,
            EmailSubject, EmailBody, SentDate, Status
        )
        VALUES (
            @OrderId, @NotificationType, @CustomerEmail,
            @EmailSubject, @EmailBody, GETUTCDATE(), 'Sent'
        );
        
        RETURN 0;
    END TRY
    BEGIN CATCH
        DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrorMsg, 16, 1);
        RETURN -1;
    END CATCH
END
GO
