# config.py

FACEBOOK_CONFIG = {
    'page_id': '103640919705348',
    'access_token': 'EAAPbnmTSpmoBQfwzHHATXE1eE7ZCJAtgosEagKjC7I70oZCmMOR1kf8co1ZBSBFKD80oZCtBZBcZCTOwnqY7A3d0qImy4DmvoNvprJOncdH2GqR45NmJ1ZB1EQ0bIN40VZBOtNZCgVfKzrUXy6iGPnj5IyPsCxSZCyaracl6lC3HcZCNyTKi71wDy8hZBZAv0XiiLKFTjIJsZD',
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
