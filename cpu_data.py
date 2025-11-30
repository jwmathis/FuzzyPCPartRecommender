# cpu_data.py

cpu_dataset = [
    # Intel 14th/13th Gen (LGA 1700)
    {'model': 'Intel Core i9-14900K', 'price_usd': 569.00, 'single_core_score': 4930, 'multi_core_score': 63900, 'socket': 'LGA 1700', 'ram_gen': 'DDR5'},
    {'model': 'Intel Core i7-14700K', 'price_usd': 389.00, 'single_core_score': 4590, 'multi_core_score': 50800, 'socket': 'LGA 1700', 'ram_gen': 'DDR5'},
    {'model': 'Intel Core i5-14600K', 'price_usd': 279.00, 'single_core_score': 4300, 'multi_core_score': 36500, 'socket': 'LGA 1700', 'ram_gen': 'DDR5'},
    {'model': 'Intel Core i5-13400F', 'price_usd': 185.00, 'single_core_score': 3820, 'multi_core_score': 25000, 'socket': 'LGA 1700', 'ram_gen': 'DDR4/DDR5'}, # Note: These support both

    # AMD Ryzen 7000 Series (AM5)
    {'model': 'AMD Ryzen 9 7950X3D', 'price_usd': 690.00, 'single_core_score': 4170, 'multi_core_score': 61000, 'socket': 'AM5', 'ram_gen': 'DDR5'},
    {'model': 'AMD Ryzen 7 7800X3D', 'price_usd': 350.00, 'single_core_score': 4120, 'multi_core_score': 34400, 'socket': 'AM5', 'ram_gen': 'DDR5'},
    {'model': 'AMD Ryzen 5 7600X', 'price_usd': 199.00, 'single_core_score': 3980, 'multi_core_score': 25800, 'socket': 'AM5', 'ram_gen': 'DDR5'},

    # Older High-End/Mid-Range (AM4)
    {'model': 'AMD Ryzen 9 5950X', 'price_usd': 499.00, 'single_core_score': 3500, 'multi_core_score': 45700, 'socket': 'AM4', 'ram_gen': 'DDR4'},
    {'model': 'AMD Ryzen 7 5800X3D', 'price_usd': 315.00, 'single_core_score': 3480, 'multi_core_score': 26000, 'socket': 'AM4', 'ram_gen': 'DDR4'},

    # Older Intel (LGA 1200 - Placeholder for a 3-5 year range)
    {'model': 'Intel Core i9-11900K', 'price_usd': 299.00, 'single_core_score': 3500, 'multi_core_score': 28000, 'socket': 'LGA 1200', 'ram_gen': 'DDR4'},
]