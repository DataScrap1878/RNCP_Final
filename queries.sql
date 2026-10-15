-- Exemples de requêtes 

-- Requête SQL 1 - Récuperer les bases de données (DB bookworld_reference)
select country_code, country_name, region, is_active from countries;
select channel_code, channel_name, channel_group, acquisition_cost_gbp, is_active from channels;


-- Requête SQL 2 - Filtre : Récupérer les pays actifs (DB bookworld_reference)
select country_name as nom_pays from countries where is_active = 1;

-- Requête SQL 3 - Aggregation : Récuperer les ventes totales des pays non inclus dans le referentiel (DB bookworld_final)
select sales.country_code as nom_pays, count(*) as nb_commandes, round(sum("revenu (GBP)"),2) as revenue_gbp from sales
left join countries on countries.country_code = sales.country_code
where countries.country_code is null
group by sales.country_code;

-- Requête SQL 4 - Contrôle de l’indicateur : CA EUR par pays (recalcul en SQL)
with CTE as (select sales.country_code, countries.country_name, sales."revenu (EUR)"
from sales
left join countries on countries.country_code = sales.country_code)
select CTE.country_code as 'code_pays', coalesce(CTE.country_name,'Inconnu (' || CTE.country_code || ')') as 'nom_pays', round(sum(CTE."revenu (EUR)"),2) as 'Total en EUR'
from CTE
group by CTE.country_code, cte.country_name
ORDER by cte.country_code Asc;



