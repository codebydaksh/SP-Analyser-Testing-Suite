CREATE PROCEDURE dbo.GetUserOrders
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        o.OrderId,
        o.OrderDate,
        o.TotalAmount,
        u.UserName
    FROM dbo.Orders o
    INNER JOIN dbo.Users u ON o.UserId = u.UserId
    WHERE o.UserId = 1
    ORDER BY o.OrderDate DESC;
    
    INSERT INTO dbo.AccessLog (UserId, AccessTime, Action)
    VALUES (1, GETDATE(), 'GetOrders');
END
GO
