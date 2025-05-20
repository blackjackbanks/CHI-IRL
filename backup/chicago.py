import pandas as pd
from meetup import get_meetup_events
from mhub import get_mhub_events
from luma import get_luma_group_events
from common import mark_online_events, upload_to_gsheets, get_gsheet_df, create_event_markdown, create_discord_list, scrape_user_events
from datetime import datetime

organization_df = get_gsheet_df("Organizations")
meetup_groups = organization_df['Meetup'].tolist()
meetup_groups = list(set([x for x in meetup_groups if len(x) > 0]))

luma_groups = organization_df['LuMa'].tolist()
luma_groups = list(set([x for x in luma_groups if len(x) > 0]))

luma_groups

