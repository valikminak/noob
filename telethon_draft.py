from telethon import TelegramClient
from telethon.tl.functions.contacts import UnblockRequest, BlockRequest
api_id = 20467597
api_hash = 'd58054f8523d1ed375f0428dc4b40ee7'
client = TelegramClient('anon', api_id, api_hash)

res = ['@penelopa_top_model', '@markus_of0', '@martadella_assist', '@assist_albina_sfs', '@rimma_onlyfans', '@rimma_onlyfans', '@Cassablanca_sfs', '@roxy_top_sfs', '@marfa_only_sfs', '@historiya_of_sfs', '@tutta_top_sfs', '@anna_manager_of', '@michel_onlyfans', '@roxy_top_sfs', '@miss_meladie_sfs', '@brenda_assist_of', '@violetta_manager_of', '@violetta_manager_of', '@bora_sfs', '@mirinda_top_sfs', '@gg_sfs_lilu', '@omega_onlyfans', '@michel_onlyfans', '@Ginnna_assistant', '@violetta_manager_of', '@Eva_honey_sfs', '@yammy_sfs', '@yammy_sfs', '@Ravina_manager_SFS', '@mirinda_top_sfs', '@Charlotte_assistant', '@karmen_agency', '@donna_sfs', '@donna_sfs', '@margarita_sfs_ass', '@tiffany_co_onlyfans', '@miss_black_onlyfans', '@julia_manager_sfs', '@minerva_manager_of_sfs', '@gg_sfs_lilu', '@margarita_sfs_ass', '@rimma_onlyfans', '@Cassablanca_sfs', '@violetta_manager_of', '@Marsi_of_sfs', '@julia_manager_sfs', '@omega_onlyfans']


async def main():
    for username in res:
        user = await client.get_input_entity(username)
        request = BlockRequest(id=user)
        await client(request)
with client:
    client.loop.run_until_complete(main())