# motherboard_data.py

motherboard_dataset = [
    # AMD AM5 (Ryzen 7000/8000 series) - Requires DDR5
    {'model': 'ASUS ROG STRIX X670E-E GAMING WIFI', 'price_usd': 499.00, 'socket': 'AM5', 'ram_gen': 'DDR5', 'chipset': 'X670E'},
    {'model': 'MSI MAG B650 TOMAHAWK WIFI', 'price_usd': 199.00, 'socket': 'AM5', 'ram_gen': 'DDR5', 'chipset': 'B650'},
    {'model': 'Gigabyte AORUS ELITE B650', 'price_usd': 179.00, 'socket': 'AM5', 'ram_gen': 'DDR5', 'chipset': 'B650'},

    # Intel LGA 1700 (12th/13th/14th Gen)
    {'model': 'MSI MPG Z790 CARBON WIFI', 'price_usd': 399.00, 'socket': 'LGA 1700', 'ram_gen': 'DDR5', 'chipset': 'Z790'},
    {'model': 'ASUS PRIME B760-PLUS', 'price_usd': 159.00, 'socket': 'LGA 1700', 'ram_gen': 'DDR5', 'chipset': 'B760'},
    {'model': 'Gigabyte H610M S2H', 'price_usd': 99.00, 'socket': 'LGA 1700', 'ram_gen': 'DDR4', 'chipset': 'H610'}, # Lower-end DDR4 board

    # Older AMD AM4 (Ryzen 3000/5000 series) - Primarily DDR4
    {'model': 'ASUS ROG STRIX X570-F GAMING', 'price_usd': 249.00, 'socket': 'AM4', 'ram_gen': 'DDR4', 'chipset': 'X570'},
    {'model': 'Gigabyte B550 GAMING X V2', 'price_usd': 129.00, 'socket': 'AM4', 'ram_gen': 'DDR4', 'chipset': 'B550'},
]