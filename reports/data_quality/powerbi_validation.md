# Power BI export validation

All fact keys matched unique, non-null dimensions. Forecast evaluation has one row per holdout date. No .pbix file is generated; follow powerbi/power_query_steps.md in Power BI Desktop.

|                     |    rows | sha256                                                           |
|:--------------------|--------:|:-----------------------------------------------------------------|
| dim_product         |    5304 | 1a6c9ed07f90c5d61f71c01104d43dc0ce77b7ad663de512312f4a8c1a54a691 |
| dim_customer        |    5943 | daad3d94869fb92ef9f672b6d41bae4468cbacec6817ef90e2d318e8e16655a3 |
| dim_country         |      43 | bc10710debca82346d47a0547a6453bd6b4bb688beeb9fcae11443a254b89d84 |
| dim_date            |     739 | 7ee9dba7a285bcf218083ef95f4dfb87b29073747c91c31a656c7b811c2d7c9f |
| fact_sales          | 1044843 | 530cddb2a2f984541ce0776a5b12eec112a827f9fbe74249cc67a4cbda95edcc |
| forecast_evaluation |     142 | 812d5a33f4e94c207222d9c35ebbf048804b5d5ef7c1dcd447414ecc7720acf2 |