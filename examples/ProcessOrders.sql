CREATE PROCEDURE dbo.ProcessOrders
AS
BEGIN
    DECLARE @counter INT = 0;
    
    IF @counter < 10
    BEGIN
        SELECT * FROM Orders;
    END
    
    WHILE @counter < 5
    BEGIN
        UPDATE Orders SET Processed = 1 WHERE OrderId = @counter;
        SET @counter = @counter + 1;
    END
    
    SELECT * FROM OrderSummary;
END
