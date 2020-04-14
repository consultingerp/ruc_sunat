
CREATE OR REPLACE VIEW vst_kardex_fisico AS 
 SELECT stock_move.product_uom, 
        CASE
            WHEN sl.usage::text = 'supplier'::text THEN 0::double precision
            ELSE 
            CASE
                WHEN original.id <> uomt.id THEN round((stock_move.price_unit * original.factor::double precision / uomt.factor::double precision)::numeric, 6)::double precision
                ELSE stock_move.price_unit
            END
        END AS price_unit, 
        CASE
            WHEN uom_uom.id <> uomt.id THEN round((stock_move.product_uom_qty::double precision * uomt.factor::double precision / uom_uom.factor::double precision)::numeric, 6)
            ELSE stock_move.product_uom_qty
        END AS product_qty, 
    stock_move.location_id, stock_move.location_dest_id, 
    stock_move.picking_type_id, stock_move.product_id, stock_move.picking_id, 
    0 AS invoice_id, 
        CASE
            WHEN stock_picking.use_kardex_date THEN stock_picking.kardex_date::timestamp without time zone
            ELSE 
            stock_picking.kardex_date::timestamp without time zone                
        END AS date, 
    stock_picking.name, stock_picking.partner_id, 
    case when tok.id is not null then tok.code || '-' || tok.name else '' end AS guia, null as analitic_id, stock_move.id, 
    product_product.default_code, stock_move.state AS estado
   FROM stock_move
   join uom_uom ON stock_move.product_uom = uom_uom.id
   JOIN stock_picking ON stock_move.picking_id = stock_picking.id
   JOIN stock_picking_type ON stock_picking.picking_type_id = stock_picking_type.id
   JOIN stock_location sl ON sl.id = stock_move.location_dest_id
   JOIN product_product ON stock_move.product_id = product_product.id
   JOIN product_template ON product_product.product_tmpl_id = product_template.id
   join uom_uom uomt ON uomt.id = product_template.uom_id
   join uom_uom original ON original.id = product_template.uom_id
   LEFT JOIN type_operation_kardex tok ON stock_picking.type_operation_sunat_id = tok.id
  WHERE (stock_move.state::text = ANY (ARRAY['done'::text, 'assigned'::text])) AND product_template.type::text = 'product'::text AND stock_move.picking_id IS NOT NULL AND product_template.active;
