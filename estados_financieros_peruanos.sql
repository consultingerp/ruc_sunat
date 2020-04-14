--------------------------------------------------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS tablefunc;
------------------------------------------account_efective_rep_it---------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.get_efective_flow(
	periodo_ini character varying,
	periodo_fin character varying,
	period_saldo_inicial character varying,
	company integer)
    RETURNS TABLE(name character varying, efective_group character varying, total numeric, efective_order integer) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
AS $BODY$
BEGIN

RETURN QUERY

SELECT * 
FROM (
	SELECT
	T.account_efective_type_name,
	T.grupo,
	sum(T.balance) as balance,
	T.orden
	FROM(
		SELECT
		vst_d.cuenta AS account_code,
		ati.name AS account_efective_type_name,
		sum(vst_d.haber) as ingreso,
		sum(vst_d.debe) as egreso, 
		sum(haber-debe) as balance,
		ati."group" as grupo,
		ati.order as orden
		FROM vst_diariog vst_d 
		LEFT JOIN account_account aa ON aa.id = vst_d.account_id
		LEFT JOIN account_efective_type ati ON ati.id = aa.account_type_cash_id
		WHERE vst_d.move_id IN(
			SELECT move_id FROM vst_diariog
			WHERE LEFT(cuenta,2)='10' AND RIGHT(periodo,2) NOT IN ('00','13')
			AND (fecha between $1 AND $2)
			AND company_id = $4)
		AND LEFT(vst_d.cuenta,2)<>'10'
		GROUP BY vst_d.cuenta,ati.name,ati."group",ati.order
	) T
	GROUP BY T.account_efective_type_name,T.grupo,T.orden
	UNION ALL
	SELECT 
	'Saldo EFECT y EQUIV de EFECT al inicio del Ejercicio' as account_efective_type_name,
	'E7'::varchar as grupo,
	sum(haber-debe) as balance,
	-1::integer as orden
	FROM vst_diariog vst_d
	LEFT JOIN account_account aa ON aa.id = vst_d.account_id
	LEFT JOIN account_efective_type ati ON ati.id = aa.account_type_cash_id
	WHERE LEFT(cuenta,2)='10' AND periodo = $3
	AND aa.company_id = $4 
	GROUP BY ati.name,ati."group",ati.order)T
ORDER BY T.orden;

END;
$BODY$;

-------------------------------------------------account_efective_rep_it------------------------------------------------------------------

-------------------------------------------------account_htf1_report------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f1_register(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_register(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer)
  RETURNS TABLE(mayor text, cuenta character varying, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select left(aa.code,2) as mayor,aa.code as cuenta,aa.name as nomenclatura,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and aa.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and aa.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and aa.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and aa.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and aa.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun,
	ati.name as rubro
	from(
		select
	vd.account_id,
	sum(vd.debe) as debe,
	sum(vd.haber) as haber,
	case 
		when sum(vd.debe) > sum(vd.haber) 
		then sum(vd.debe) - sum(vd.haber)
		else 0
	end as saldo_deudor,
	case
		when sum(vd.haber) > sum(vd.debe)
		then sum(vd.haber) - sum(vd.debe)
		else 0
	end as saldo_acreedor
	from vst_diariog vd
	where vd.company_id = $3 and (cast(vd.periodo as int ) between cast($1 as int ) and cast($2 as int ))
	group by vd.account_id
	)T
	left join account_account aa on aa.id = T.account_id
	left join account_type_it ati on ati.id = aa.account_type_it_id
	order by left(aa.code,2),aa.code
	;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION public.get_f1_register(character varying, character varying, integer)
  OWNER TO openpg;
-------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f1_balance(character varying,character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f1_balance(
    IN period_from character varying,
    IN period_to character varying,
    IN company integer)
  RETURNS TABLE(mayor text, nomenclatura character varying, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric) AS
$BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe,T.haber,
		   T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f1r.mayor,
		ag.name,
		ag.id,
		sum(f1r.debe) as debe,
		sum(f1r.haber) as haber,
		case 
			when sum(f1r.debe) > sum(f1r.haber) 
			then sum(f1r.debe) - sum(f1r.haber)
			else 0
		end as saldo_deudor,
		case
			when sum(f1r.haber) > sum(f1r.debe)
			then sum(f1r.haber) - sum(f1r.debe)
			else 0
		end as saldo_acreedor
		from get_f1_register($1,$2,$3) f1r
		left join account_group ag on ag.code_prefix = f1r.mayor
    	group by f1r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id
	order by T.mayor;
                  
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION public.get_f1_balance(character varying, character varying, integer)
  OWNER TO openpg;

-------------------------------------------------account_htf1_report------------------------------------------------------------------

-------------------------------------------------account_htf2_report------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f2_register(character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f2_register(
	period character varying,
	company integer)
    RETURNS TABLE(mayor text, cuenta character varying, nomenclatura character varying, debe_inicial numeric, haber_inicial numeric, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric, rubro character varying) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
    
AS $BODY$
BEGIN
RETURN QUERY 
	select 
		left(cta.code,2) as mayor,
		cta.code as cuenta,
		cta.name as nomenclatura,
		t.debeini as debe_inicial,
		t.haberini as haber_inicial,
		t.debep as debe,
		t.haberp as haber,
		t.saldo_deudor,
		t.saldo_acreedor,
			case 
				when t.saldo_deudor > 0 and cta.clasification_sheet = '0'
				then t.saldo_deudor
				else 0.00
			end as activo,
			case 
				when t.saldo_acreedor > 0 and cta.clasification_sheet = '0'
				then t.saldo_acreedor
				else 0.00
			end as pasivo,
			case 
				when (t.saldo_deudor > 0 and cta.clasification_sheet = '1') or 
					 (t.saldo_deudor > 0 and cta.clasification_sheet = '3')
				then t.saldo_deudor
				else 0.00
			end as perdinat,
			case 
				when (t.saldo_acreedor > 0 and cta.clasification_sheet = '1') or
					 (t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
				then t.saldo_acreedor
				else 0.00
			end as ganannat,
			case 
				when (t.saldo_deudor > 0 and cta.clasification_sheet = '2') or
					 (t.saldo_deudor > 0 and cta.clasification_sheet = '3')
				then T.saldo_deudor
				else 0.00
			end as perdifun,
			case 
				when (t.saldo_acreedor > 0 and cta.clasification_sheet = '2') or
					 (t.saldo_acreedor > 0 and cta.clasification_sheet = '3')
				then t.saldo_acreedor
				else 0.00
			end as gananfun,
			tipo.name as rubro
		from 
		(

		select 
		distinct integral.account_id,
		coalesce(saldoini.debeini,0.00) as debeini,
		coalesce(saldoini.haberini,0.00) as haberini,
		coalesce(saldoac.debeac,0.00) as debep,
		coalesce(saldoac.haberac,0.00) as haberp,
		case when 
			coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00) > coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)
		then
			(coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)) - (coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00))
		else	0.00
		end as saldo_deudor,

		case when 
			  coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00) > coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00)
		then 
			 ( coalesce(saldoini.haberini,0.00)+ coalesce(saldoac.haberac,0.00)) - (coalesce(saldoini.debeini,0.00)+ coalesce(saldoac.debeac,0.00))
		else 0.00
		end as saldo_acreedor
		from vst_diariog integral 
		left join 
		-- ACA PONER LOS PARAMETROS PARA COMPAÑIA Y PERIODO INICIAL QUE SERA EL AÑO DEL PERIODO ELEGIDO ( CUATRO DIGITOS PRIMERO) CONCATENADO CON '00'
		(select diario_a.account_id,sum(diario_a.debe) as debeini,sum(diario_a.haber) as haberini from vst_diariog diario_a where diario_a.company_id=$2 and cast(diario_a.periodo as int) = cast(left($1,4) || '00' as int) group by diario_a.account_id)
		saldoini on saldoini.account_id=integral.account_id
		left join 
		-- ACA PONER LOS PARAMETROS PARA COMPAÑIA Y PERIODO HASTA EL CUAL SE QUIERE ,  SIN CONSIDERAR EL PERIODO INICIAL 
		(select diario_b.account_id,sum(diario_b.debe) as debeac,sum(diario_b.haber) as haberac from 
		vst_diariog diario_b where diario_b.company_id=$2 and cast(diario_b.periodo as int) <= cast($1 as int) and cast(diario_b.periodo as int) <> cast(left($1,4) || '00' as int) group by diario_b.account_id)
		saldoac on saldoac.account_id=integral.account_id
		-- EN ESTE WHERE VA EL PARAMETRO DE LA COMPAÑIA Y DE LOS PERIODOS INICAL SIEMPRE 00  Y FINAL PORQUE SE NECESITA EL ACUMULADO DE LAS CUENTAS 
		where company_id=1 and (cast(periodo as int) between cast(left($1,4) || '00' as int) and cast($1 as int))
		) t
		left join account_account cta on cta.id=t.account_id                 
		left join account_type_it tipo on tipo.id=cta.account_type_it_id
		order by left(cta.code,2),cta.code;              
END; $BODY$;

ALTER FUNCTION public.get_f2_register(character varying, integer)
    OWNER TO openpg;
-------------------------------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS public.get_f2_balance(character varying,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_f2_balance(
	period character varying,
	company integer)
    RETURNS TABLE(mayor text, nomenclatura character varying, debe_inicial numeric, haber_inicial numeric, debe numeric, haber numeric, saldo_deudor numeric, saldo_acreedor numeric, activo numeric, pasivo numeric, perdinat numeric, ganannat numeric, perdifun numeric, gananfun numeric) 
    LANGUAGE 'plpgsql'

    COST 100
    VOLATILE 
    ROWS 1000
    
AS $BODY$
BEGIN

RETURN QUERY 
    
	select T.mayor,T.name,T.debe_inicial,T.haber_inicial,
		   T.debe,T.haber,T.saldo_deudor,T.saldo_acreedor,
	case 
		when T.saldo_deudor > 0 and ag.clasification_sheet = '0'
		then T.saldo_deudor
		else 0
	end as activo,
	case 
		when T.saldo_acreedor > 0 and ag.clasification_sheet = '0'
		then T.saldo_acreedor
		else 0
	end as pasivo,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '1') or 
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdinat,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '1') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as ganannat,
	case 
		when (T.saldo_deudor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_deudor > 0 and ag.clasification_sheet = '3')
		then T.saldo_deudor
		else 0
	end as perdifun,
	case 
		when (T.saldo_acreedor > 0 and ag.clasification_sheet = '2') or
			 (T.saldo_acreedor > 0 and ag.clasification_sheet = '3')
		then T.saldo_acreedor
		else 0
	end as gananfun
	from(
		select
		f2r.mayor,
		ag.name,
		ag.id,
		sum(f2r.debe_inicial) as debe_inicial,
		sum(f2r.haber_inicial) as haber_inicial,
		sum(f2r.debe) as debe,
		sum(f2r.haber) as haber,
		case 
			when sum(f2r.debe) + sum(f2r.debe_inicial) > sum(f2r.haber) + sum(f2r.haber_inicial) 
			then (sum(f2r.debe) + sum(f2r.debe_inicial)) - (sum(f2r.haber) + sum(f2r.haber_inicial))
			else 0
		end as saldo_deudor,
		case
			when sum(f2r.haber) + sum(f2r.haber_inicial) > sum(f2r.debe) + sum(f2r.debe_inicial)
			then (sum(f2r.haber) + sum(f2r.haber_inicial)) - (sum(f2r.debe) + sum(f2r.debe_inicial))
			else 0
		end as saldo_acreedor
		from get_f2_register($1,$2) f2r
		left join account_group ag on ag.code_prefix = f2r.mayor
    	group by f2r.mayor,ag.name,ag.id)T
	inner join account_group ag on ag.id = T.id
	order by T.mayor;
                  
END; $BODY$;

ALTER FUNCTION public.get_f2_balance(character varying, integer)
    OWNER TO openpg;

-------------------------------------------------account_htf2_report------------------------------------------------------------------