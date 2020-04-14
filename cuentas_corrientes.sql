------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------
----------Obtenemos los saldos por fecha de documento,fecha de documento y si el balance es 0 , fecha contable ,fecha contable y si el balance es 0

DROP FUNCTION IF EXISTS public.get_saldos(date, date, integer, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_saldos(
    IN date_ini date,
    IN date_fin date,
    IN id_company integer,
    IN query_type integer)
  RETURNS TABLE(id bigint, periodo text, fecha_con text, libro character varying, voucher character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, debe numeric, haber numeric, saldo_mn numeric, saldo_me numeric,aml_ids integer[], journal_id integer, account_id integer, partner_id integer, move_id integer, move_line_id integer, company_id integer) AS
$BODY$
BEGIN
	IF query_type = 0 THEN
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 1 THEN
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 2 THEN 
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha_doc::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	ELSIF query_type = 3 THEN 
		RETURN QUERY 
		SELECT row_number() OVER () AS id,t.*
		   FROM ( select 
		b2.periodo, 
		b2.fecha as fecha_con, 
		b2.libro, 
		b2.voucher, 
		b2.td_partner, 
		b2.doc_partner, 
		b2.partner, 
		b2.td_sunat,
		b2.nro_comprobante, 
		b2.fecha_doc,
		b2.fecha_ven,
		b2.cuenta,
		b1.sum_debe as debe,
		b1.sum_haber as haber,
		b1.sum_balance as saldo_mn,
		b1.sum_importe_me as saldo_me,
		b1.aml_ids,
		b2.journal_id,
		b2.account_id,
		b2.partner_id,
		b2.move_id,
		b2.move_line_id,
		b2.company_id
		from(
		select a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante,
		sum(a1.debe) as sum_debe, sum(a1.haber) as sum_haber, sum(a1.balance) as sum_balance, 
		sum(a1.importe_me) as sum_importe_me, min(a1.move_line_id) as min_line_id,
		array_agg(aml.id) as aml_ids
		from vst_diariog a1
		inner join account_move_line aml on aml.id = a1.move_line_id
		inner join account_move am on am.id = aml.move_id
		left join account_account a2 on a2.id = a1.account_id
		where (a2.is_document_an = True) and (a1.fecha_doc::date between $1::date and $2::date) and a1.company_id = $3
		group by a1.partner_id, a1.account_id, a1.td_sunat, a1.nro_comprobante
		having sum(a1.balance) <> 0
		)b1
		left join vst_diariog  b2 on b2.move_line_id = b1.min_line_id
		order by b2.partner, b2.cuenta, b2.td_sunat, b2.nro_comprobante, b2.fecha_doc) t;
	END IF;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

---------------------------------------------------------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos el detalle de comprobante, donde los parametros son fecha inicial, fecha final y company_id

CREATE OR REPLACE FUNCTION public.get_saldo_detalle(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying,td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, cuenta character varying, debe numeric, haber numeric,balance numeric,importe_me numeric, saldo numeric, saldo_me numeric, partner_id integer, account_id integer) AS
$BODY$
DECLARE 
    var_r record;
    quiebre TEXT;
    contador INT;
BEGIN
   contador = 0 ;
   saldo = 0;
   saldo_me = 0;
   FOR var_r IN(
        select 
		vst_d.periodo, 
		vst_d.fecha, 
		vst_d.libro, 
		vst_d.voucher,
		vst_d.td_partner, 
		vst_d.doc_partner, 
		vst_d.partner, 
		vst_d.td_sunat, 
		vst_d.nro_comprobante, 
		vst_d.fecha_doc, 
		vst_d.fecha_ven, 
		vst_d.cuenta, 
		vst_d.debe, 
		vst_d.haber,
		vst_d.balance,
		vst_d.importe_me,
		vst_d.partner_id,
		vst_d.account_id
		from vst_diariog vst_d
		left join account_account aa on aa.id = vst_d.account_id
		where aa.is_document_an = True and (vst_d.fecha::date between fec_ini::date and fec_fin::date) and vst_d.company_id = id_compannia
		order by vst_d.partner_id,vst_d.account_id,vst_d.td_sunat,vst_d.nro_comprobante,vst_d.fecha       
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante);
            contador = contador + 1;
        END IF;
        
        -- Si los registros son los mismos
        IF quiebre =  concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante) THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        -- Si cambia, reinicio el saldo y actualizo
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := concat(var_r.partner_id,var_r.account_id,var_r.td_sunat,var_r.nro_comprobante);
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        END IF;

        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        cuenta  = var_r.cuenta ;
        debe = var_r.debe ;
        haber  = var_r.haber ;
        balance = var_r.balance ;
        importe_me  = var_r.importe_me ;
        partner_id = var_r.partner_id ;
        account_id = var_r.account_id ;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------account_balance_doc_rep_it---------------------------------------------------------------
