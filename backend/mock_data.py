"""
Mock data for testing without actually scraping
"""

MOCK_APARTMENTS = [
    {
        'url': 'https://www.booli.se/annons/12345',
        'address': 'Strandvägen 7A, Östermalm, Stockholm',
        'agent': 'Anna Andersson',
        'agency': 'Svensk Fastighetsförmedling',
        'sold_price': '8 500 000 kr',
        'sold_date': '2024-01-15',
    },
    {
        'url': 'https://www.booli.se/annons/12346',
        'address': 'Karlavägen 45, Östermalm, Stockholm',
        'agent': 'Erik Eriksson',
        'agency': 'Länsförsäkringar Fastighetsförmedling',
        'sold_price': '9 200 000 kr',
        'sold_date': '2024-01-20',
    },
    {
        'url': 'https://www.booli.se/annons/12347',
        'address': 'Linnégatan 18, Östermalm, Stockholm',
        'agent': 'Maria Svensson',
        'agency': 'Notar Mäklare',
        'sold_price': '8 750 000 kr',
        'sold_date': '2024-01-22',
    },
    {
        'url': 'https://www.booli.se/annons/12348',
        'address': 'Valhallavägen 88, Östermalm, Stockholm',
        'agent': 'Johan Nilsson',
        'agency': 'Bjurfors',
        'sold_price': '9 800 000 kr',
        'sold_date': '2024-01-25',
    },
    {
        'url': 'https://www.booli.se/annons/12349',
        'address': 'Grev Turegatan 30, Östermalm, Stockholm',
        'agent': 'Lisa Johansson',
        'agency': 'Erik Olsson Fastighetsförmedling',
        'sold_price': '8 900 000 kr',
        'sold_date': '2024-01-28',
    },
]


def get_mock_apartments():
    """Return mock apartment data"""
    return MOCK_APARTMENTS.copy()
