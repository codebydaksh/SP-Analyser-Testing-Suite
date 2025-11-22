EXEC tSQLt.NewTestClass 'Testdbo';
GO

CREATE PROCEDURE [Testdbo].[test_BasicExecution]
AS
BEGIN
    -- Arrange
    -- Act
    EXEC dbo 1, 1, 'test', 1, 1;
    -- Assert
    -- Add assertions here
END;
GO

CREATE PROCEDURE [Testdbo].[test_NullParameters]
AS
BEGIN
    -- Test with NULL parameters
    EXEC dbo NULL, NULL, NULL, NULL, NULL;
END;
GO
