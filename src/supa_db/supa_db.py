from supabase import create_client


class SupaDB:
    def __init__(self, database_url: str, jwt: str):
        self.client = create_client(database_url, jwt)

    def get_user_name(self, user_id: str) -> str:
        result = self.client.table('profiles') \
            .select('name') \
            .eq('id', user_id) \
            .execute()
        return result.data[0]['name'] if result.data else "Unknown"
