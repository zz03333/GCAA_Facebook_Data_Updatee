# config.py

FACEBOOK_CONFIG = {
    'page_id': '103640919705348',
    'access_token': 'EAAPbnmTSpmoBQEIJ3H6KCC1ZA6YFROcXcZAHJAhf2g8eoG4cyParQdkxKXRYyb8ww9vFGIDogWbDqO8kAwY9aVjrV0zfJdqNuDQDLA5JiKas095i3od2NZCHLAgMTo7CFf9kXGza1okttRrAPHZBe70GXUEAlnzh1yZBFIHPmFFkTImusaTBN6F94uIeNsFZBfjD8ms9kZD',
    'api_version': 'v23.0'
}

DB_PATH = 'data/engagement_data.db'

# Page Level Metrics
PAGE_METRICS = [
    'page_impressions_unique',
    'page_post_engagements',
    'page_video_views',
    'page_actions_post_reactions_total'
]

PAGE_LIFETIME_METRICS = [
    'fan_count',
]

# Post Level Metrics
# 更新日期: 2025-12-12
# 移除已棄用的指標: post_impressions, post_impressions_organic, post_impressions_paid
POST_METRICS = [
    'post_clicks',
    'post_impressions_unique',  # 保留 (觸及人數)
    # 'post_impressions',  # ✗ 已棄用
    # 'post_impressions_organic',  # ✗ 已棄用
    # 'post_impressions_paid',  # ✗ 已棄用
    'post_video_views',
    'post_video_views_organic',
    'post_video_views_paid',
    'post_reactions_like_total',
    'post_reactions_love_total',
    'post_reactions_wow_total',
    'post_reactions_haha_total',
    'post_reactions_sorry_total',
    'post_reactions_anger_total'
]
