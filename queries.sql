-- Exemples de requêtes 

-- Requête SQL 1 - Enrichissement : Récuperer les bases de données (DB bookworld_reference)
select country_code, country_name, region, is_active from countries;
select channel_code, channel_name, channel_group, acquisition_cost_gbp, is_active from channels;


-- Requête SQL 2 - Filtre : Récupérer les pays actifs (DB bookworld_reference)
select country_name from countries where is_active = 1;

-- Requête SQL 3 - Aggregation : Récuperer les ventes totales des pays non inclus dans le referentiel (DB bookworld_final)
select sales.country_code, count(*), round(sum("revenu (GBP)"),2) from sales
left join countries on countries.country_code = sales.country_code
where countries.country_code is null
group by sales.country_code;

-- Requête SQL 4 - Aggregation : Ventilation des ventes par pays et par canal
with CTE as (select sales.channel_code,sales.country_code, countries.country_name, sales."revenu (EUR)", channels.channel_name
from sales
left join channels on channels.channel_code = sales.channel_code
left join countries on countries.country_code = sales.country_code)
select CTE.country_code as 'Code Pays', coalesce(CTE.country_name,'Inconnu') as 'Nom Pays', CTE.channel_name as 'Canal', round(sum(CTE."revenu (EUR)"),2) as 'Total en EUR'
from CTE
group by CTE.country_code, cTE.channel_name
ORDER by cte.country_code Asc;
