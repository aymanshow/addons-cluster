
{
    'name' : "Pos Fiscal Printer",
    'category' : "Test",
    'version' : "1.0",
    'depends' : ['point_of_sale'],
    'author' : "Me",
    'description' : """Fiscal Printer""",
    'init_xml': [
        'data/http_helper_data.xml'
     ],
    'data' : [        
        'view/pos_fiscal_printer_view.xml',
        'view/pos_fiscal_printer_action_menu.xml',
        'view/point_of_sale_view.xml',
    ],
}
