select rank, count(*) from 
(select (data->'highestAchievedSeasonTier')::varchar as rank from 
	(select 
	json_array_elements(participants_data::json) as data from matchinfo) t1
	) t2 group by rank;



--USED in PSQL
--create tables for champion IDs
--JSON expansion function takes a little while to run, but it's reasonable

--Fix due to forgetfulness

UPDATE matchinfo
SET
Ban2 = (teams_data->1->'bans'->0->'championId')::VARCHAR::INTEGER,
Ban4 = (teams_data->1->'bans'->1->'championId')::VARCHAR::INTEGER,
Ban6 = (teams_data->1->'bans'->2->'championId')::VARCHAR::INTEGER;

DROP TABLE IF EXISTS championIds;

select championId::integer, count(*), row_number() OVER 
(ORDER BY championId::integer)
INTO championIds
from 
(select (data->'championId')::varchar as championId from 
	(select json_array_elements(participants_data::json) 
	as data from matchinfo) t1) t2 group by championId order by championId;

--extrapolate competition rank from games
--unranked/NA: 0
--bronze: 1
--silver: 2
--gold: 3
--platinum: 4
--diamond: 5
--master: 6
--challenger: 7


--category will correspond to the rounded average of these

--first, create table with the following format:

/*match_id, position, position_rank, position_rank_numeric*/ --and...
/*match_id, position, championId, fixed_championId*/
--use championIds table join to get fixed_championId

DROP TABLE IF EXISTS match_userdata;
SELECT game_id,
		(data#>'{stats,winner}')::VARCHAR::BOOLEAN AS wonGame,
		(data->'championId')::VARCHAR::INTEGER AS championId,
		(data#>'{timeline,lane}')::VARCHAR as lane,
		(data->'participantId')::VARCHAR::INTEGER as participantId,
	(data->'highestAchievedSeasonTier')::varchar AS tier 
	INTO match_userdata
	FROM  
	(SELECT game_id, json_array_elements(participants_data::json)
		as data from matchinfo) t1;

--update table to have coded ranking value
ALTER TABLE match_userdata ADD tier_code INTEGER;

UPDATE match_userdata SET tier_code=
CASE WHEN tier='"UNRANKED"' THEN 0
WHEN tier='"BRONZE"' THEN 1
WHEN tier='"SILVER"' THEN 2
WHEN tier='"GOLD"' THEN 3
WHEN tier='"PLATINUM"' THEN 4
WHEN tier='"DIAMOND"' THEN 5
WHEN tier='"MASTER"' THEN 6
WHEN tier='"CHALLENGER"' THEN 7
ELSE -1
END;


--update table to have fixed Champion ID

ALTER TABLE match_userdata ADD fixed_championId INTEGER;

UPDATE match_userdata 
SET fixed_championId = championIds.row_number
FROM championIds 
WHERE match_userdata.championId=championIds.championId;

--create table with rounded average rank

DROP TABLE IF EXISTS match_rankings;

SELECT game_id, round(avg(tier_code)) as averageRanking
INTO match_rankings
FROM match_userdata group by game_id;


--create new table with the following format:

/*match_id, champion_ids AS array, bans AS array, 
> individual ranks AS numeric array, average_rank (rounded), game_type,
> date_of_match, team1_win (True/False)*/

DROP TABLE IF EXISTS match_summary;

SELECT mi.game_id, Ban1, Ban2, Ban3, Ban4, Ban5, Ban6,
(participants_data#>'{0,stats,winner}')::VARCHAR::BOOLEAN as team1win,
mu.champIds AS champIds,
mr.averageRanking as averageRanking,
mu.tierCodes as tierCodes,
gi.game_timestamp AS timestamp,
gi.subtype AS match_type,
-1 AS learning_role
INTO 
match_summary
FROM 
matchinfo as mi
	INNER JOIN
	match_rankings as mr ON mr.game_id = mi.game_id
	INNER JOIN
	(select game_id,
	array_agg(fixed_championId ORDER BY participantId) as champIds,
	array_agg(tier_code ORDER BY participantId) as tierCodes,
	array_agg(participantId) as participantIds--used to ensure order was proper 
	FROM match_userdata
	GROUP BY game_id) mu ON mu.game_id = mi.game_id
	INNER JOIN gameinfo AS gi on gi.game_id = mi.game_id
ORDER BY game_id;

--fix the Ban ids
UPDATE match_summary
SET 
Ban1 = championIds.row_number
FROM championIds
WHERE Ban1=championIds.championId;

UPDATE match_summary
SET 
Ban2 = championIds.row_number
FROM championIds
WHERE Ban2=championIds.championId;

UPDATE match_summary
SET 
Ban3 = championIds.row_number
FROM championIds
WHERE Ban3=championIds.championId;

UPDATE match_summary
SET 
Ban4 = championIds.row_number
FROM championIds
WHERE Ban4=championIds.championId;

UPDATE match_summary
SET 
Ban5 = championIds.row_number
FROM championIds
WHERE Ban5=championIds.championId;

UPDATE match_summary
SET 
Ban6 = championIds.row_number
FROM championIds
WHERE Ban6=championIds.championId;

UPDATE match_summary
SET 
learning_role = round(random()*12);


--diagnostic queries...

--noticed some missing bans from games...not present in teams_data either
select count(*), year, month from (select EXTRACT(year from timestamp)
 as year, EXTRACT(month from timestamp) as month from match_summary 
 WHERE Ban1 is null and match_type='RANKED_SOLO_5x5') t1 
group by year, month order by year, month;

/*
 count | year | month 
-------+------+-------
     1 | 2014 |     5
     1 | 2015 |     3
     1 | 2015 |     6
     1 | 2015 |     7
     2 | 2015 |     8
     2 | 2015 |     9
   146 | 2016 |     1
   586 | 2016 |     2
    24 | 2016 |     3
*/

--let's see what the counts are for various category types
select count(*), match_type, averageranking 
from match_summary 
WHERE match_type ~'^RANKED' 
GROUP BY match_type, averageranking 
order by averageranking, match_type;

/*
 count |   match_type    | averageranking 
-------+-----------------+----------------
   975 | RANKED_SOLO_5x5 |              0
    83 | RANKED_TEAM_3x3 |              0
   269 | RANKED_TEAM_5x5 |              0
 14533 | RANKED_SOLO_5x5 |              1
    85 | RANKED_TEAM_3x3 |              1
   368 | RANKED_TEAM_5x5 |              1
 18272 | RANKED_SOLO_5x5 |              2
    34 | RANKED_TEAM_3x3 |              2
   123 | RANKED_TEAM_5x5 |              2
  9053 | RANKED_SOLO_5x5 |              3
     6 | RANKED_TEAM_3x3 |              3
    32 | RANKED_TEAM_5x5 |              3
  1505 | RANKED_SOLO_5x5 |              4
     3 | RANKED_TEAM_5x5 |              4
   198 | RANKED_SOLO_5x5 |              5
     9 | RANKED_SOLO_5x5 |              6
*/

select count(*), match_type, averageranking 
from match_summary 
WHERE match_type ~'^RANKED' AND EXTRACT(year from timestamp)=2016
GROUP BY match_type, averageranking 
order by averageranking, match_type;

/*
 count |   match_type    | averageranking 
-------+-----------------+----------------
   902 | RANKED_SOLO_5x5 |              0
    72 | RANKED_TEAM_3x3 |              0
   248 | RANKED_TEAM_5x5 |              0
 14024 | RANKED_SOLO_5x5 |              1
    81 | RANKED_TEAM_3x3 |              1
   359 | RANKED_TEAM_5x5 |              1
 17645 | RANKED_SOLO_5x5 |              2
    32 | RANKED_TEAM_3x3 |              2
   122 | RANKED_TEAM_5x5 |              2
  8868 | RANKED_SOLO_5x5 |              3
     6 | RANKED_TEAM_3x3 |              3
    32 | RANKED_TEAM_5x5 |              3
  1478 | RANKED_SOLO_5x5 |              4
     3 | RANKED_TEAM_5x5 |              4
   198 | RANKED_SOLO_5x5 |              5
     9 | RANKED_SOLO_5x5 |              6
*/
