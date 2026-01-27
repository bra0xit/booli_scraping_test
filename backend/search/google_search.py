from googleapiclient.discovery import build


class GoogleSearcher:
    """Handle Google Custom Search API queries"""

    def __init__(self, api_key, cse_id):
        """
        Initialize Google Custom Search

        Args:
            api_key: Google API key
            cse_id: Custom Search Engine ID
        """
        self.api_key = api_key
        self.cse_id = cse_id
        self.service = build("customsearch", "v1", developerKey=api_key)

    def find_realtor_listing(self, address, agent=None, agency=None):
        """
        Search for the original realtor listing

        Args:
            address: Apartment address
            agent: Real estate agent name
            agency: Real estate agency name

        Returns:
            URL of the most relevant realtor listing, or None
        """
        if not address:
            return None

        # Build search query
        query_parts = [address]

        if agent:
            query_parts.append(agent)

        if agency:
            query_parts.append(agency)

        query = ' '.join(query_parts)

        # Add Swedish realtor keywords
        query += ' mäklare bostad'

        try:
            # Execute search
            result = self.service.cse().list(
                q=query,
                cx=self.cse_id,
                num=5  # Get top 5 results
            ).execute()

            if 'items' in result and len(result['items']) > 0:
                # Filter for known Swedish realtor domains
                realtor_domains = [
                    'hemnet.se',
                    'svenskfast.se',
                    'notar.se',
                    'lansfast.se',
                    'maklarringen.se',
                    'bjurfors.se',
                    'fantastiskfast.se',
                    'erikolsson.se',
                    'husmanhagberg.se'
                ]

                # First, try to find a result from known realtor sites
                for item in result['items']:
                    link = item.get('link', '')
                    if any(domain in link for domain in realtor_domains):
                        return link

                # If no known realtor site found, return first result
                return result['items'][0].get('link')

            return None

        except Exception as e:
            print(f"Error searching for {address}: {str(e)}")
            return None
