--------------------------------CONFIGURAR DECIMALES A DOS DIGITOS------------------------------------------------------
--ALTER TABLE account_move_line ALTER COLUMN debit TYPE numeric(64,2);
--ALTER TABLE account_move_line ALTER COLUMN credit TYPE numeric(64,2);
--ALTER TABLE account_move_line ALTER COLUMN amount_currency TYPE numeric(64,2);
--ALTER TABLE account_move_line ALTER COLUMN amount_residual TYPE numeric(64,2);
--ALTER TABLE account_move_line ALTER COLUMN amount_residual_currency TYPE numeric(64,2);
-------------------------------------------------account_report_menu_it------------------------------------------------------------------
--vista padre de donde salen todas las lineas contables, solo si son publicadas
DROP VIEW IF EXISTS public.vst_diariog CASCADE;

CREATE OR REPLACE VIEW public.vst_diariog AS 
 SELECT row_number() OVER () AS id,
    tt.periodo,
    tt.fecha,
    tt.libro,
    tt.voucher,
    tt.cuenta,
    tt.debe,
    tt.haber,
    tt.balance,
    tt.moneda,
    tt.tc,
    tt.importe_me,
    tt.cta_analitica,
    tt.glosa,
    tt.td_partner,
    tt.doc_partner,
    tt.partner,
    tt.td_sunat,
    tt.nro_comprobante,
    tt.fecha_doc,
    tt.fecha_ven,
    tt.col_reg,
    tt.monto_reg,
    tt.medio_pago,
    tt.estado,
    tt.ple_diario,
    tt.ple_compras,
    tt.ple_ventas,
    tt.journal_id,
    tt.account_id,
    tt.partner_id,
    tt.registro,
    tt.move_id,
    tt.move_line_id,
    tt.company_id,
    tt.col_reg_id,
    tt.perception_date,
    tt.code_cta_analitica
   FROM ( SELECT 
	    CASE
            WHEN a1.is_opening_close = TRUE AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '0101' THEN to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '00'
            WHEN a1.is_opening_close = TRUE AND to_char(a1.date::timestamp with time zone, 'mmdd'::text) = '1231' THEN to_char(a1.date::timestamp with time zone, 'yyyy'::text) || '13'
            ELSE to_char(a1.date::timestamp with time zone, 'yyyymm'::text)
	    END AS periodo,
            to_char(a1.date::timestamp with time zone, 'yyyy/mm/dd'::text) AS fecha,
            a3.code AS libro,
            a1.name AS voucher,
            a4.code AS cuenta,
            a2.debit AS debe,
            a2.credit AS haber,
            a2.balance,
		CASE
		    WHEN a2.currency_id IS NULL THEN 'PEN'::character varying
		    ELSE a5.name
		END AS moneda,
            a2.tc,
            a2.amount_currency AS importe_me,
            a2.analytic_account_id AS cta_analitica,
            a1.glosa,
            a7.code_sunat AS td_partner,
            a6.vat AS doc_partner,
            a6.name AS partner,
            a8.code AS td_sunat,
            a2.nro_comp AS nro_comprobante,
            a1.invoice_date AS fecha_doc,
            a2.date_maturity AS fecha_ven,
            a10.name AS col_reg,
            a2.tax_amount_it AS monto_reg,
            a1.td_payment_id AS medio_pago,
            a1.state AS estado,
            a1.ple_state AS ple_diario,
            a1.campo_41_purchase AS ple_compras,
            a1.campo_34_sale AS ple_ventas,
            a1.journal_id,
            a2.account_id,
            a2.partner_id,
            a3.register_sunat AS registro,
            a1.id AS move_id,
            a2.id AS move_line_id,
            a1.company_id,
            a10.id AS col_reg_id,
            a1.perception_date,
            a11.name AS code_cta_analitica
           FROM account_move a1
             LEFT JOIN account_move_line a2 ON a2.move_id = a1.id
             LEFT JOIN account_journal a3 ON a3.id = a1.journal_id
             LEFT JOIN account_account a4 ON a4.id = a2.account_id
             LEFT JOIN res_currency a5 ON a5.id = a2.currency_id
             LEFT JOIN res_partner a6 ON a6.id = a2.partner_id
             LEFT JOIN l10n_latam_identification_type a7 ON a7.id = a6.l10n_latam_identification_type_id
             LEFT JOIN einvoice_catalog_01 a8 ON a8.id = a2.type_document_id
             LEFT JOIN account_account_tag_account_move_line_rel a9 ON a9.account_move_line_id = a2.id
             LEFT JOIN account_account_tag a10 ON a10.id = a9.account_account_tag_id
             LEFT JOIN account_analytic_account a11 ON a11.id = a2.analytic_account_id
          WHERE a1.state::text = 'posted'::text
          ORDER BY (date_part('month'::text, a1.date)), a3.code, a1.name, a2.debit DESC, a4.code) tt;

----------------------------------------------------------------------------------------------------------------
---------Con esta vista se obtiene la primera linea de los documentos relacionados, sirve para el reporte de 
---------registro de ventas, compras, percepciones.

CREATE OR REPLACE VIEW public.doc_rela_pri AS 
 SELECT doc_invoice_relac.move_id,
    min(doc_invoice_relac.id) AS min
   FROM doc_invoice_relac
  GROUP BY doc_invoice_relac.move_id;

----------------------------------------------------------------------------------------------------------------
----------Esta vista obtiene el libro mayor, reporte con todas las cuentas

DROP VIEW IF EXISTS public.vst_mayor CASCADE;

CREATE OR REPLACE VIEW public.vst_mayor AS 
 SELECT tt.periodo,
    tt.fecha,
    tt.libro,
    tt.voucher,
    tt.cuenta,
    tt.debe,
    tt.haber,
    tt.balance,
    tt.moneda,
    tt.tc,
    tt.importe_me,
    tt.code_cta_analitica,
    tt.glosa,
    tt.td_partner,
    tt.doc_partner,
    tt.partner,
    tt.td_sunat,
    tt.nro_comprobante,
    tt.fecha_doc,
    tt.fecha_ven,
    tt.company_id,
    tt.account_id
   FROM ( SELECT vst_diariog.periodo,
            to_date(vst_diariog.fecha, 'yyyy/mm/dd'::text) AS fecha,
            vst_diariog.libro,
            vst_diariog.voucher,
            vst_diariog.cuenta,
            vst_diariog.debe,
            vst_diariog.haber,
            vst_diariog.balance,
            vst_diariog.moneda,
            vst_diariog.tc,
            vst_diariog.importe_me,
            vst_diariog.code_cta_analitica,
            vst_diariog.glosa,
            vst_diariog.td_partner,
            vst_diariog.doc_partner,
            vst_diariog.partner,
            vst_diariog.td_sunat,
            vst_diariog.nro_comprobante,
            vst_diariog.fecha_doc,
            vst_diariog.fecha_ven,
            vst_diariog.company_id,
            vst_diariog.account_id
           FROM vst_diariog
          ORDER BY vst_diariog.cuenta, vst_diariog.periodo, vst_diariog.fecha) tt;

--------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos el libro mayor con el detalle de las cuentas y haciendo sumatoria de los
----------balances, de parametros estan la fecha inicial, fecha final y company_id. Se usa la vista vst_mayor

DROP FUNCTION IF EXISTS public.get_mayor_detalle(date,date,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_mayor_detalle(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, moneda character varying, tc numeric, importe_me numeric, code_cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, company_id integer, account_id integer, saldo numeric, saldo_me numeric) AS
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
        select * from (
           SELECT * FROM VST_MAYOR WHERE VST_MAYOR.fecha>= fec_ini 
                    AND  VST_MAYOR.fecha <= fec_fin AND VST_MAYOR.company_id = id_compannia
            union all
            SELECT "left"(to_char((fec_ini-1)::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo, fec_ini - 1, '' as libro, '' as voucher, VST_MAYOR.cuenta, 0 as debe, 0 as haber,
            SUM (VST_MAYOR.balance) AS balance, '' AS moneda, 0 AS tc, SUM (VST_MAYOR.importe_me) AS importe_me, '' as code_cta_analitica, '' as glosa,
            '' AS td_partner, '' AS doc_partner, '' AS partner, '' AS td_sunat, '' AS nro_comprobante, null::date AS fecha_doc, null::date AS fecha_ven, 0 as company_id, 
            0 AS account_id   
            FROM VST_MAYOR WHERE VST_MAYOR.fecha < fec_ini AND VST_MAYOR.company_id = id_compannia
                            AND  EXTRACT (YEAR FROM VST_MAYOR.fecha) = EXTRACT (YEAR FROM fec_ini)
            group by VST_MAYOR.cuenta
         )T
                ORDER BY cuenta, periodo, fecha
               
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := var_r.cuenta ;
            contador = contador + 1;
        END IF;
        
        -- Si los registros son de la misma cuenta
        IF quiebre =  var_r.cuenta THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        -- Si la cuenta cambia, reinicio el saldo y actualizo el quiebre
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := var_r.cuenta ;
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        END IF;
        
        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        cuenta  = var_r.cuenta ;
        debe = var_r.debe ;
        haber = var_r.haber;
        balance = var_r.balance ;
        moneda = var_r.moneda ;
        tc  = var_r.tc ;
        importe_me  = var_r.importe_me ;
        code_cta_analitica = var_r.code_cta_analitica ;
        glosa = var_r.glosa ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        company_id = var_r.company_id ;
        account_id  = var_r.account_id ;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

------------------------------------------------------------------------------------------------------------------
----------Esta vista obtiene el libro Auxiliar de Bancos, reporte solo con las cuentas que empiezan
----------con 104 y 107

DROP VIEW IF EXISTS public.vst_bancos CASCADE;

CREATE OR REPLACE VIEW public.vst_bancos AS 
 SELECT tt.periodo,
    tt.fecha,
    tt.libro,
    tt.voucher,
    tt.cuenta,
    tt.debe,
    tt.haber,
    tt.balance,
    tt.moneda,
    tt.tc,
    tt.importe_me,
    tt.code_cta_analitica,
    tt.glosa,
    tt.td_partner,
    tt.doc_partner,
    tt.partner,
    tt.td_sunat,
    tt.nro_comprobante,
    tt.fecha_doc,
    tt.fecha_ven,
    tt.company_id,
    tt.account_id
   FROM ( SELECT vst_diariog.periodo,
            to_date(vst_diariog.fecha, 'yyyy-mm-dd'::text) AS fecha,
            vst_diariog.libro,
            vst_diariog.voucher,
            vst_diariog.cuenta,
            vst_diariog.debe,
            vst_diariog.haber,
            vst_diariog.balance,
            vst_diariog.moneda,
            vst_diariog.tc,
            vst_diariog.importe_me,
            vst_diariog.code_cta_analitica,
            vst_diariog.glosa,
            vst_diariog.td_partner,
            vst_diariog.doc_partner,
            vst_diariog.partner,
            vst_diariog.td_sunat,
            vst_diariog.nro_comprobante,
            vst_diariog.fecha_doc,
            vst_diariog.fecha_ven,
            vst_diariog.company_id,
            vst_diariog.account_id
           FROM vst_diariog
          WHERE "left"(vst_diariog.cuenta::text, 3) = ANY (ARRAY['104'::text, '107'::text])
          ORDER BY vst_diariog.cuenta, vst_diariog.periodo, vst_diariog.fecha) tt;

----------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos el auxiliar de bancos con el detalle de las cuentas y haciendo sumatoria de los
----------balances, de parametros estan la fecha inicial, fecha final y company_id. Se usa la vista vst_bancos

DROP FUNCTION IF EXISTS public.get_bancos(date,date,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_bancos(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, moneda character varying, tc numeric, importe_me numeric, code_cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, company_id integer, account_id integer, saldo numeric, saldo_me numeric) AS
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
        select * from (
           SELECT * FROM VST_BANCOS WHERE VST_BANCOS.fecha>= fec_ini 
                    AND  VST_BANCOS.fecha <= fec_fin AND VST_BANCOS.company_id = id_compannia
            union all
            SELECT "left"(to_char((fec_ini-1)::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo, fec_ini - 1, '' as libro, '' as voucher, VST_BANCOS.cuenta, 0 as debe, 0 as haber,
            SUM (VST_BANCOS.balance) AS balance, '' AS moneda, 0 AS tc, SUM (VST_BANCOS.importe_me) AS importe_me, '' as code_cta_analitica, '' as glosa,
            '' AS td_partner, '' AS doc_partner, '' AS partner, '' AS td_sunat, '' AS nro_comprobante, null::date AS fecha_doc, null::date AS fecha_ven, 0 as company_id, 
            0 AS account_id   
            FROM VST_BANCOS WHERE VST_BANCOS.fecha < fec_ini 
                            AND  EXTRACT (YEAR FROM VST_BANCOS.fecha) = EXTRACT (YEAR FROM fec_ini)
            group by VST_BANCOS.cuenta
         )T
                ORDER BY cuenta, periodo, fecha
               
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := var_r.cuenta ;
            contador = contador + 1;
        END IF;
        
        -- Si los registros son de la misma cuenta
        IF quiebre = var_r.cuenta THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        -- Si la cuenta cambia, reinicio el saldo y actualizo el quiebre
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := var_r.cuenta ;
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        END IF;
        
        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        cuenta  = var_r.cuenta ;
        debe = var_r.debe ;
        haber = var_r.haber;
        balance = var_r.balance ;
        moneda = var_r.moneda ;
        tc  = var_r.tc ;
        importe_me  = var_r.importe_me ;
        code_cta_analitica = var_r.code_cta_analitica ;
        glosa = var_r.glosa ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        company_id = var_r.company_id ;
        account_id  = var_r.account_id ;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

-------------------------------------------------------------------------------------------------------------
----------Esta vista obtiene el libro Caja y Bancos, reporte solo con las cuentas que empiezan
----------con 10

DROP VIEW IF EXISTS public.vst_caja_bancos CASCADE;

CREATE OR REPLACE VIEW public.vst_caja_bancos AS 
 SELECT tt.periodo,
    tt.fecha,
    tt.libro,
    tt.voucher,
    tt.cuenta,
    tt.debe,
    tt.haber,
    tt.balance,
    tt.moneda,
    tt.tc,
    tt.importe_me,
    tt.code_cta_analitica,
    tt.glosa,
    tt.td_partner,
    tt.doc_partner,
    tt.partner,
    tt.td_sunat,
    tt.nro_comprobante,
    tt.fecha_doc,
    tt.fecha_ven,
    tt.company_id,
    tt.account_id
   FROM ( SELECT vst_diariog.periodo,
            to_date(vst_diariog.fecha, 'yyyy-mm-dd'::text) AS fecha,
            vst_diariog.libro,
            vst_diariog.voucher,
            vst_diariog.cuenta,
            vst_diariog.debe,
            vst_diariog.haber,
            vst_diariog.balance,
            vst_diariog.moneda,
            vst_diariog.tc,
            vst_diariog.importe_me,
            vst_diariog.code_cta_analitica,
            vst_diariog.glosa,
            vst_diariog.td_partner,
            vst_diariog.doc_partner,
            vst_diariog.partner,
            vst_diariog.td_sunat,
            vst_diariog.nro_comprobante,
            vst_diariog.fecha_doc,
            vst_diariog.fecha_ven,
            vst_diariog.company_id,
            vst_diariog.account_id
           FROM vst_diariog
          WHERE "left"(vst_diariog.cuenta::text, 2) = '10'::text
          ORDER BY vst_diariog.cuenta, vst_diariog.periodo, vst_diariog.fecha) tt;

------------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos el libro caja y bancos con el detalle de las cuentas y haciendo sumatoria de los
----------balances, de parametros estan la fecha inicial, fecha final y company_id. Se usa la vista vst_caja_bancos

DROP FUNCTION IF EXISTS public.get_caja_bancos(date,date,integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_caja_bancos(
    IN fec_ini date,
    IN fec_fin date,
    IN id_compannia integer)
  RETURNS TABLE(periodo character varying, fecha date, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, moneda character varying, tc numeric, importe_me numeric, code_cta_analitica character varying, glosa character varying, td_partner character varying, doc_partner character varying, partner character varying, td_sunat character varying, nro_comprobante character varying, fecha_doc date, fecha_ven date, company_id integer, account_id integer, saldo numeric, saldo_me numeric) AS
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
        select * from (
           SELECT * FROM VST_CAJA_BANCOS WHERE VST_CAJA_BANCOS.fecha>= fec_ini 
                    AND  VST_CAJA_BANCOS.fecha <= fec_fin AND VST_CAJA_BANCOS.company_id = id_compannia
            union all
            SELECT "left"(to_char((fec_ini-1)::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo, fec_ini - 1, '' as libro, '' as voucher, VST_CAJA_BANCOS.cuenta, 0 as debe, 0 as haber,
            SUM (VST_CAJA_BANCOS.balance) AS balance, '' AS moneda, 0 AS tc, SUM (VST_CAJA_BANCOS.importe_me) AS importe_me, '' as code_cta_analitica, '' as glosa,
            '' AS td_partner,'' AS doc_partner, '' AS partner, '' AS td_sunat, '' AS nro_comprobante, null::date AS fecha_doc, null::date AS fecha_ven, 0 as company_id, 
            0 AS account_id   
            FROM VST_CAJA_BANCOS WHERE VST_CAJA_BANCOS.fecha < fec_ini 
                            AND  EXTRACT (YEAR FROM VST_CAJA_BANCOS.fecha) = EXTRACT (YEAR FROM fec_ini)
            group by VST_CAJA_BANCOS.cuenta
         )T
                ORDER BY cuenta, periodo, fecha
               
               )
   LOOP
        -- Obtiene por unica vez el valor del primer registro
        IF contador = 0 THEN 
            quiebre := var_r.cuenta ;
            contador = contador + 1;
        END IF;
        
        -- Si los registros son de la misma cuenta
        IF quiebre =  var_r.cuenta THEN
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        -- Si la cuenta cambia, reinicio el saldo y actualizo la cuenta 
        ELSE
            saldo = 0;
            saldo_me = 0;
            quiebre := var_r.cuenta ;
            saldo = saldo + var_r.balance;
            saldo_me = saldo_me +  var_r.importe_me;
        END IF;
        
        periodo = var_r.periodo ;
        fecha = var_r.fecha ;
        libro = var_r.libro ;
        voucher = var_r.voucher ;
        cuenta  = var_r.cuenta ;
        debe = var_r.debe ;
        haber = var_r.haber;
        balance = var_r.balance ;
        moneda = var_r.moneda ;
        tc  = var_r.tc ;
        importe_me  = var_r.importe_me ;
        code_cta_analitica = var_r.code_cta_analitica ;
        glosa = var_r.glosa ;
        td_partner = var_r.td_partner ;
        doc_partner = var_r.doc_partner;
        partner = var_r.partner;
        td_sunat = var_r.td_sunat ;
        nro_comprobante  = var_r.nro_comprobante ;
        fecha_doc = var_r.fecha_doc ;
        fecha_ven  = var_r.fecha_ven ;
        company_id = var_r.company_id ;
        account_id  = var_r.account_id ;
        
   RETURN NEXT;
   END LOOP;
END; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;

-----------------------------------------------------------------------------------------------------------------
----------Con esta vista obtendremos las columnas de todos los impuestos de Compras y posicionamos el monto en la columna
----------correcta, dejando en 0 a las demas, es necesario para el reporte de Registro de Compras

CREATE OR REPLACE VIEW public.vst_compras_1 AS 
 SELECT dg.move_id,
    sum(
        CASE
            WHEN at.record_shop::text = '1'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS base1,
    sum(
        CASE
            WHEN at.record_shop::text = '2'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS base2,
    sum(
        CASE
            WHEN at.record_shop::text = '3'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS base3,
    sum(
        CASE
            WHEN at.record_shop::text = '4'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS cng,
    sum(
        CASE
            WHEN at.record_shop::text = '5'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS isc,
    sum(
        CASE
            WHEN at.record_shop::text = '6'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS otros,
    sum(
        CASE
            WHEN at.record_shop::text = '7'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS igv1,
    sum(
        CASE
            WHEN at.record_shop::text = '8'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS igv2,
    sum(
        CASE
            WHEN at.record_shop::text = '9'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS igv3
   FROM vst_diariog dg
     JOIN account_account_tag at ON at.id = dg.col_reg_id
  WHERE dg.registro::text = '1'::text AND dg.col_reg_id IS NOT NULL
  GROUP BY dg.move_id;

---------------------------------------------------------------------------------------------------------------
----------Con esta vista obtendremos el Registro de Compras, incluyendo las columnas de impuestos
DROP VIEW IF EXISTS vst_compras_1_1 CASCADE;

CREATE OR REPLACE VIEW public.vst_compras_1_1 AS 
 SELECT row_number() OVER () AS id,
    tt.periodo,
    tt.fecha_cont,
    tt.libro,
    tt.voucher,
    tt.fecha_e,
    tt.fecha_v,
    tt.td,
    tt.serie,
    tt.anio,
    tt.numero,
    tt.tdp,
    tt.docp,
    tt.namep,
    tt.base1,
    tt.base2,
    tt.base3,
    tt.cng,
    tt.isc,
    tt.otros,
    tt.igv1,
    tt.igv2,
    tt.igv3,
    tt.total,
    tt.name,
    tt.monto_me,
    tt.currency_rate,
    tt.fecha_det,
    tt.comp_det,
    tt.f_doc_m,
    tt.td_doc_m,
    tt.serie_m,
    tt.numero_m,
    tt.glosa,
    tt.company,
    tt.am_id,
    tt.partner_id
   FROM ( SELECT "left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo,
            am.date AS fecha_cont,
            aj.code AS libro,
            am.name AS voucher,
            am.invoice_date AS fecha_e,
            am.invoice_date_due AS fecha_v,
            ec1.code AS td,
            CASE
                WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 1)
                ELSE ''
            END
            AS serie,
            to_char(am.invoice_date , 'yyyy') as anio,
            CASE
                WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 2)
                ELSE split_part(am.ref, '-', 1)
            END
            AS numero,
            lit.code_sunat AS tdp,
            rp.vat AS docp,
            rp.name AS namep,
            mc.base1,
            mc.base2,
            mc.base3,
            mc.cng,
            mc.isc,
            mc.otros,
            mc.igv1,
            mc.igv2,
            mc.igv3,
            mc.base1 + mc.base2 + mc.base3 + mc.cng + mc.isc + mc.otros + mc.igv1 + mc.igv2 + mc.igv3 AS total,
            rc.name,
                CASE
                    WHEN rc.name::text <> 'PEN'::text THEN am.amount_total
                    ELSE 0::numeric(12,2)
                END AS monto_me,
            am.currency_rate,
            am.date_detraccion AS fecha_det,
            am.voucher_number AS comp_det,
            dr.date AS f_doc_m,
            eic1.code AS td_doc_m,
            CASE
                WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)
                ELSE ''
            END
            AS serie_m,
            CASE
                WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)
                ELSE split_part(dr.nro_comprobante, '-', 1)
            END
            AS numero_m,
            am.glosa,
            am.company_id AS company,
            am.id AS am_id,
            rp.id AS partner_id
           FROM account_move am
             LEFT JOIN account_journal aj ON aj.id = am.journal_id
             LEFT JOIN res_partner rp ON rp.id = am.partner_id
             LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
             LEFT JOIN einvoice_catalog_01 ec1 ON ec1.id = am.type_document_id
             LEFT JOIN ( SELECT a2.type_document_id,
                    a2.date,
                    a2.nro_comprobante,
                    a2.amount_currency,
                    a2.amount,
                    a2.bas_amount,
                    a2.tax_amount,
                    a2.id,
                    a2.move_id
                   FROM doc_rela_pri a1
                     LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = am.id
             LEFT JOIN einvoice_catalog_01 eic1 ON eic1.id = dr.type_document_id
             LEFT JOIN vst_compras_1 mc ON mc.move_id = am.id
             LEFT JOIN res_currency rc ON rc.id = am.currency_id
          WHERE aj.register_sunat::text = '1'::text AND am.state::text = 'posted'::text
          ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.name) tt;

-------------------------------------------------------------------------------------------------------------------
----------Con esta vista obtendremos las columnas de todos los impuestos de Ventas y posicionamos el monto en la columna
----------correcta, dejando en 0 a las demas, es necesario para el reporte de Registro de Ventas

CREATE OR REPLACE VIEW public.vst_ventas_1 AS 
 SELECT dg.move_id,
    sum(
        CASE
            WHEN at.record_sale::text = '1'::text THEN - dg.monto_reg
            ELSE 0::numeric
        END) AS exp,
    sum(
        CASE
            WHEN at.record_sale::text = '2'::text THEN - dg.monto_reg
            ELSE 0::numeric
        END) AS venta_g,
    sum(
        CASE
            WHEN at.record_sale::text = '3'::text THEN - dg.monto_reg
            ELSE 0::numeric
        END) AS inaf,
    sum(
        CASE
            WHEN at.record_sale::text = '4'::text THEN - dg.monto_reg
            ELSE 0::numeric
        END) AS exo,
    sum(
        CASE
            WHEN at.record_sale::text = '5'::text THEN - dg.monto_reg
            ELSE 0::numeric
        END) AS isc_v,
    sum(
        CASE
            WHEN at.record_sale::text = '6'::text THEN - dg.monto_reg
            ELSE 0::numeric
        END) AS otros_v,
    sum(
        CASE
            WHEN at.record_sale::text = '7'::text THEN - dg.monto_reg
            ELSE 0::numeric
        END) AS igv_v
   FROM vst_diariog dg
     JOIN account_account_tag at ON at.id = dg.col_reg_id
  WHERE dg.registro::text = '2'::text AND dg.col_reg_id IS NOT NULL
  GROUP BY dg.move_id;

-------------------------------------------------------------------------------------------------------------------
----------Con esta vista obtendremos el Registro de Ventas, incluyendo las columnas de impuestos
DROP VIEW IF EXISTS vst_ventas_1_1 CASCADE;

CREATE OR REPLACE VIEW public.vst_ventas_1_1 AS 
 SELECT row_number() OVER () AS id,
    tt.periodo,
    tt.fecha_cont,
    tt.libro,
    tt.voucher,
    tt.fecha_e,
    tt.fecha_v,
    tt.td,
    tt.serie,
    tt.anio,
    tt.numero,
    tt.tdp,
    tt.docp,
    tt.namep,
    tt.exp,
    tt.venta_g,
    tt.inaf,
    tt.exo,
    tt.isc_v,
    tt.otros_v,
    tt.igv_v,
    tt.total,
    tt.name,
    tt.monto_me,
    tt.currency_rate,
    tt.fecha_det,
    tt.comp_det,
    tt.f_doc_m,
    tt.td_doc_m,
    tt.serie_m,
    tt.numero_m,
    tt.glosa,
    tt.company,
    tt.estado_ple,
    tt.am_id
   FROM ( SELECT "left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo,
            am.date AS fecha_cont,
            aj.code AS libro,
            am.name AS voucher,
            am.invoice_date AS fecha_e,
            am.invoice_date_due AS fecha_v,
            ec1.code AS td,
            CASE
                WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 1)
                ELSE ''
            END
            AS serie,
            to_char(am.invoice_date , 'yyyy') as anio,
            CASE
                WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 2)
                ELSE split_part(am.ref, '-', 1)
            END
            AS numero,
            lit.code_sunat AS tdp,
            rp.vat AS docp,
            rp.name AS namep,
            mv.exp,
            mv.venta_g,
            mv.inaf,
            mv.exo,
            mv.isc_v,
            mv.otros_v,
            mv.igv_v,
            mv.exp + mv.venta_g + mv.inaf + mv.exo + mv.isc_v + mv.otros_v + mv.igv_v AS total,
            rc.name,
                CASE
                    WHEN rc.name::text <> 'PEN'::text THEN am.amount_total
                    ELSE 0::numeric(12,2)
                END AS monto_me,
            am.currency_rate,
            am.date_detraccion AS fecha_det,
            am.voucher_number AS comp_det,
            dr.date AS f_doc_m,
            eic1.code AS td_doc_m,
            CASE
                WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)
                ELSE ''
            END
            AS serie_m,
            CASE
                WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)
                ELSE split_part(dr.nro_comprobante, '-', 1)
            END
            AS numero_m,
            am.glosa,
            am.company_id AS company,
            am.campo_34_sale AS estado_ple,
            am.id as am_id
           FROM account_move am
             LEFT JOIN account_journal aj ON aj.id = am.journal_id
             LEFT JOIN res_partner rp ON rp.id = am.partner_id
             LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
             LEFT JOIN einvoice_catalog_01 ec1 ON ec1.id = am.type_document_id
             LEFT JOIN ( SELECT a2.type_document_id,
                    a2.date,
                    a2.nro_comprobante,
                    a2.amount_currency,
                    a2.amount,
                    a2.bas_amount,
                    a2.tax_amount,
                    a2.id,
                    a2.move_id
                   FROM doc_rela_pri a1
                     LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = am.id
             LEFT JOIN einvoice_catalog_01 eic1 ON eic1.id = dr.type_document_id
             LEFT JOIN vst_ventas_1 mv ON mv.move_id = am.id
             LEFT JOIN res_currency rc ON rc.id = am.currency_id
          WHERE aj.register_sunat::text = '2'::text AND am.state::text = 'posted'::text
          ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.name) tt;

------------------------------------------------------------------------------------------------------------------
----------Con esta vista obtendremos las columnas de renta y retencion para lso recibos de honorarios y posicionamos el monto en la columna
----------correcta, dejando en 0 a las demas, es necesario para el reporte de Libros de Honorarios

CREATE OR REPLACE VIEW public.vst_recxhon_1 AS 
 SELECT dg.move_id,
    sum(
        CASE
            WHEN at.record_fees::text = '1'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS renta,
    sum(
        CASE
            WHEN at.record_fees::text = '2'::text THEN dg.monto_reg
            ELSE 0::numeric
        END) AS retencion
   FROM vst_diariog dg
     JOIN account_account_tag at ON at.id = dg.col_reg_id
  WHERE dg.registro::text = '3'::text AND dg.col_reg_id IS NOT NULL
  GROUP BY dg.move_id;

-------------------------------------------------------------------------------------------------------------------
----------Con esta vista obtendremos el Libro de Honorarios, incluyendo las columnas de renta y retencion

DROP VIEW IF EXISTS public.vst_recxhon_1_1 CASCADE;

CREATE OR REPLACE VIEW public.vst_recxhon_1_1 AS 
 SELECT row_number() OVER () AS id,
    tt.periodo,
    tt.libro,
    tt.voucher,
    tt.fecha_e,
    tt.fecha_p,
    tt.td,
    tt.serie,
    tt.numero,
    tt.tdp,
    tt.docp,
    tt.apellido_p,
    tt.apellido_m,
    tt.namep,
    tt.divisa,
    tt.monto_me,
    tt.tipo_c,
    tt.renta,
    tt.retencion,
    tt.neto_p,
    tt.periodo_p,
    tt.is_not_home,
    tt.c_d_imp,
    tt.company_id
   FROM ( SELECT "left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo,
            aj.code AS libro,
            am.name AS voucher,
            am.invoice_date AS fecha_e,
            am.invoice_date_due AS fecha_p,
            ec1.code AS td,
            CASE
                WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 1)
                ELSE ''
            END
            AS serie,
            CASE
                WHEN split_part(am.ref, '-', 2) <> '' THEN split_part(am.ref, '-', 2)
                ELSE split_part(am.ref, '-', 1)
            END
            AS numero,
            lit.code_sunat AS tdp,
            rp.vat AS docp,
            rp.last_name as apellido_p,
            rp.m_last_name as apellido_m,
            rp.name_p as namep,
            rc.name AS divisa,
            CASE
                WHEN rc.name::text <> 'PEN'::text THEN am.amount_total
                ELSE 0::numeric(12,2)
            END AS monto_me,
            am.currency_rate AS tipo_c,
            rh.renta,
            rh.retencion,
            rh.renta + rh.retencion AS neto_p,
            "left"(to_char(am.invoice_date_due::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo_p,
            CASE
                WHEN rp.is_not_home is null or rp.is_not_home = False THEN '1'
                ELSE '2'
            END AS is_not_home,
            rp.c_d_imp,
            am.company_id
           FROM account_move am
             LEFT JOIN account_journal aj ON aj.id = am.journal_id
             LEFT JOIN res_partner rp ON rp.id = am.partner_id
             LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
             LEFT JOIN einvoice_catalog_01 ec1 ON ec1.id = am.type_document_id
             LEFT JOIN ( SELECT a2.type_document_id,
                    a2.date,
                    a2.nro_comprobante,
                    a2.amount_currency,
                    a2.amount,
                    a2.bas_amount,
                    a2.tax_amount,
                    a2.id,
                    a2.move_id
                   FROM doc_rela_pri a1
                     LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = am.id
             LEFT JOIN einvoice_catalog_01 eic1 ON eic1.id = dr.type_document_id
             LEFT JOIN vst_recxhon_1 rh ON rh.move_id = am.id
             LEFT JOIN res_currency rc ON rc.id = am.currency_id
          WHERE aj.register_sunat::text = '3'::text AND am.state::text = 'posted'::text
          ORDER BY ("left"(to_char(am.date::timestamp with time zone, 'yyyymmdd'::text), 6)), aj.code, am.name) tt;

-------------------------------------------------------------------------------------------------------------------
---------- En esta vista obtenemos el detalle de las percepciones incluyendo datos de los documentos relacionados

CREATE OR REPLACE VIEW public.vst_percepciones AS 
 SELECT row_number() OVER () AS id,
    a1.periodo AS periodo_con,
    "left"(to_char(a1.perception_date::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo_percep,
    a1.perception_date AS fecha_uso,
    a1.libro,
    a1.voucher,
    a1.td_sunat AS tipo_per,
    a1.doc_partner AS ruc_agente,
    a1.partner,
    CASE
        WHEN split_part(a1.nro_comprobante, '-', 2) <> '' THEN split_part(a1.nro_comprobante, '-', 1)
        ELSE ''
    END
    AS serie_cp,
    CASE
        WHEN split_part(a1.nro_comprobante, '-', 2) <> '' THEN split_part(a1.nro_comprobante, '-', 2)
        ELSE split_part(a1.nro_comprobante, '-', 1)
    END
    AS numero_cp,
    a1.fecha_doc AS fecha_com_per,
    a1.monto_reg AS percepcion,
    a2.nro_comprobante,
    a2.date AS fecha_cp,
    a2.amount AS montof,
    a1.move_id AS am_id,
    a1.move_line_id AS aml_id,
    a1.company_id
   FROM vst_diariog a1
     LEFT JOIN ( SELECT b2.code,
            b1.date,
            b1.nro_comprobante,
            b1.amount,
            b1.move_id
           FROM doc_invoice_relac b1
             LEFT JOIN einvoice_catalog_01 b2 ON b2.id = b1.type_document_id) a2 ON a2.move_id = a1.move_id
  WHERE a1.col_reg::text = 'PER'::text;

-------------------------------------------------------------------------------------------------------------------
----------En esta vista obtenemos el detalle de solo las percepciones 

CREATE OR REPLACE VIEW public.vst_percepciones_sp AS 
 SELECT row_number() OVER () AS id,
    a1.periodo AS periodo_con,
    "left"(to_char(a1.perception_date::timestamp with time zone, 'yyyymmdd'::text), 6) AS periodo_percep,
    a1.perception_date AS fecha_uso,
    a1.libro,
    a1.voucher,
    a1.td_sunat AS tipo_per,
    a1.doc_partner AS ruc_agente,
    a1.partner,
    CASE
        WHEN split_part(a1.nro_comprobante, '-', 2) <> '' THEN split_part(a1.nro_comprobante, '-', 1)
        ELSE ''
    END
    AS serie_cp,
    CASE
        WHEN split_part(a1.nro_comprobante, '-', 2) <> '' THEN split_part(a1.nro_comprobante, '-', 2)
        ELSE split_part(a1.nro_comprobante, '-', 1)
    END
    AS numero_cp,
    a1.fecha_doc AS fecha_com_per,
    a1.monto_reg AS percepcion,
    a1.move_id AS am_id,
    a1.move_line_id AS aml_id,
    a1.company_id
   FROM vst_diariog a1
  WHERE a1.col_reg::text = 'PER'::text;

-------------------------------------------------account_report_menu_it------------------------------------------------------------------

------------------------------------......-------account_destinos_rep_it-----------------------------------------------------------------
----------Obtenemos el detalle de los destinos, ya sea desde una cuenta analitica o una cuenta normal donde tiene marcado el check 
----------"Tiene Destinos" en account.account

CREATE OR REPLACE VIEW public.vst_destinos AS 
 SELECT a1.periodo,
    a1.fecha,
    a1.libro,
    a1.voucher,
    a1.cuenta,
    a1.debe,
    a1.haber,
    a1.balance,
    a5.code AS cta_analitica,
    a3.code AS des_debe,
    a4.code AS des_haber,
    a1.move_id AS am_id,
    a1.move_line_id AS aml_id,
    a1.company_id
   FROM vst_diariog a1
     LEFT JOIN account_account a2 ON a2.id = a1.account_id
     LEFT JOIN account_account a3 ON a3.id = a2.a_debit
     LEFT JOIN account_account a4 ON a4.id = a2.a_credit
     LEFT JOIN account_analytic_account a5 ON a5.id = a1.cta_analitica
  WHERE a2.check_moorage = true AND (a3.code::text || a4.code::text) IS NOT NULL
UNION ALL
 SELECT b7.periodo,
    b7.fecha,
    b7.libro,
    b7.voucher,
    b7.cuenta,
        CASE
            WHEN b1.amount < 0::numeric THEN abs(b1.amount)
            ELSE 0::numeric
        END AS debe,
        CASE
            WHEN b1.amount > 0::numeric THEN b1.amount
            ELSE 0::numeric
        END AS haber,
    b7.balance,
    b4.code AS cta_analitica,
    b5.code AS des_debe,
    b6.code AS des_haber,
    b7.move_id AS am_id,
    b7.move_line_id AS aml_id,
    b7.company_id
   FROM account_analytic_line b1
     LEFT JOIN account_move_line b2 ON b2.id = b1.move_id
     LEFT JOIN account_account b3 ON b3.id = b1.general_account_id
     LEFT JOIN account_analytic_account b4 ON b4.id = b1.account_id
     LEFT JOIN account_account b5 ON b5.id = b4.a_debit
     LEFT JOIN account_account b6 ON b6.id = b4.a_credit
     LEFT JOIN vst_diariog b7 ON b7.move_line_id = b1.move_id
  WHERE b3.check_moorage = true;

  -------------------------------------------------------------------------------------------------------------------------------------------
  ----------Se crea una funcion para la vista vst_destinos, donde los parametros seran el periodo -> text y company_id ->integer

DROP FUNCTION IF EXISTS public.get_destinos(text,integer) CASCADE;

  CREATE OR REPLACE FUNCTION public.get_destinos(
    IN var_periodo text,
    IN var_company_id integer)
  RETURNS TABLE(periodo text, fecha text, libro character varying, voucher character varying, cuenta character varying, debe numeric, haber numeric, balance numeric, cta_analitica character varying, des_debe character varying, des_haber character varying, am_id integer, aml_id integer, company_id integer) AS
$BODY$
BEGIN
RETURN QUERY 
SELECT * FROM vst_destinos vst_d where vst_d.periodo = $1 and vst_d.company_id = $2;
END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100
ROWS 1000;

--------------------------------------------------------------------------------------------------------------------------------------------
----------Obtenemos el detalle de las cuentas, con su balance,y columnas para el balance por cada cuenta que empiece con los primeros dos caracteres indicados
---------- en la funcion.

DROP FUNCTION IF EXISTS public.get_summary_destinos(text,integer) CASCADE;

  CREATE OR REPLACE FUNCTION public.get_summary_destinos(
    IN var_periodo text,
    IN var_company_id integer)
  RETURNS TABLE(cuenta character varying, balance numeric, cta20 numeric, cta24 numeric, cta25 numeric, cta26 numeric, cta90 numeric, cta91 numeric, cta92 numeric, cta93 numeric, cta94 numeric, cta95 numeric, cta96 numeric, cta97 numeric, cta98 numeric, cta99 numeric) AS
$BODY$
BEGIN
RETURN QUERY 
SELECT
vst_d.cuenta,
vst_d.debe-vst_d.haber as balance,
CASE WHEN left(vst_d.des_debe,2)='20'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta20,
CASE WHEN left(vst_d.des_debe,2)='24'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta24,
CASE WHEN left(vst_d.des_debe,2)='25'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta25,
CASE WHEN left(vst_d.des_debe,2)='26'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta26,
CASE WHEN left(vst_d.des_debe,2)='90'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta90,
CASE WHEN left(vst_d.des_debe,2)='91'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta91,
CASE WHEN left(vst_d.des_debe,2)='92'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta92,
CASE WHEN left(vst_d.des_debe,2)='93'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta93,
CASE WHEN left(vst_d.des_debe,2)='94'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta94,
CASE WHEN left(vst_d.des_debe,2)='95'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta95,
CASE WHEN left(vst_d.des_debe,2)='96'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta96,
CASE WHEN left(vst_d.des_debe,2)='97'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta97,
CASE WHEN left(vst_d.des_debe,2)='98'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta98,
CASE WHEN left(vst_d.des_debe,2)='99'  THEN (vst_d.debe-vst_d.haber) ELSE 0 END AS cta99
FROM vst_destinos vst_d
WHERE vst_d.periodo = $1 AND vst_d.company_id = $2;
END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100
ROWS 1000;

---------------------------------------------------------------------------------------------------------------------------------------
----------Con esta funcion obtenemos una vista preliminar de los asientos de destino que se van a generar

DROP FUNCTION IF EXISTS public.get_asiento_destino(text, integer) CASCADE;

CREATE OR REPLACE FUNCTION public.get_asiento_destino(
    IN var_periodo text,
    IN var_company_id integer)
  RETURNS TABLE(periodo text, glosa text,cuenta character varying, name character varying, debe numeric, haber numeric, account_id integer) AS
$BODY$
BEGIN
RETURN QUERY 
select $1::text as periodo, 'Por el destino del Periodo ' || $1 as glosa, T.cuenta, aa.name, T.debe, T.haber, aa.id as account_id from (
select 
vst_d.des_debe as cuenta,
sum(vst_d.debe) as debe,
0:: numeric as haber
from vst_destinos vst_d
where vst_d.periodo = $1 and vst_d.company_id = $2
group by vst_d.des_debe

union all

select vst_d.des_haber as cuenta,
0::numeric as debe,
sum(vst_d.debe) as haber
from vst_destinos vst_d
where vst_d.periodo = $1 and vst_d.company_id = $2
group by vst_d.des_haber

union all

select vst_d.des_debe as cuenta,
0::numeric as debe,
sum(vst_d.haber) as haber
from vst_destinos vst_d
where vst_d.periodo = $1 and vst_d.company_id = $2
group by vst_d.des_debe

union all

select vst_d.des_haber as cuenta,
sum(vst_d.haber) as debe,
0::numeric as haber
from vst_destinos vst_d
where vst_d.periodo = $1 and vst_d.company_id = $2
group by vst_d.des_haber)T
left join account_account aa on aa.code = T.cuenta 
where (T.debe+T.haber) <> 0;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;


------------------------------------------account_destinos_rep_it---------------------------------------------------------------
