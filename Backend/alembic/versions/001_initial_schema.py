"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-22 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # Profiles
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.Text(), nullable=False),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('phone', sa.Text(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_profiles_email', 'profiles', ['email'])

    # Categories
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Services
    op.create_table(
        'services',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Providers
    op.create_table(
        'providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('display_name', sa.Text(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('phone_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('identity_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recommendation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('completed_jobs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_rating', sa.Numeric(3, 2), nullable=False, server_default='0'),
        sa.Column('total_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('service_radius_km', sa.Numeric(6, 2), nullable=False, server_default='5.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Provider Services
    op.create_table(
        'provider_services',
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('services.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('price_from', sa.Numeric(12, 2), nullable=True),
        sa.Column('price_to', sa.Numeric(12, 2), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Locations
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=True),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), nullable=True),
        sa.Column('label', sa.Text(), nullable=False, server_default='Primary'),
        sa.Column('locality', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=False),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('pincode', sa.Text(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('point', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_locations_point ON locations USING GIST(point);")

    # Provider Availability
    op.create_table(
        'provider_availability',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_of_week', sa.SmallInteger(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Requests
    op.create_table(
        'requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_description', sa.Text(), nullable=False),
        sa.Column('ai_parsed_requirement', postgresql.JSONB(), nullable=True),
        sa.Column('ai_confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('services.id', ondelete='SET NULL'), nullable=True),
        sa.Column('budget_min', sa.Numeric(12, 2), nullable=True),
        sa.Column('budget_max', sa.Numeric(12, 2), nullable=True),
        sa.Column('radius_km', sa.Numeric(6, 2), nullable=False, server_default='5.0'),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location', geoalchemy2.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('status', sa.Enum('open', 'matching', 'matched', 'provider_responded', 'connected', 'in_progress', 'completed', 'cancelled', 'expired', name='request_status'), nullable=False, server_default='open'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_requests_location ON requests USING GIST(location);")

    # Request Matches
    op.create_table(
        'request_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('distance_km', sa.Numeric(8, 3), nullable=True),
        sa.Column('service_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('availability_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('price_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('rating_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('trust_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('total_match_score', sa.Numeric(6, 2), nullable=False, server_default='0'),
        sa.Column('status', sa.Enum('pending', 'viewed', 'interested', 'declined', 'accepted', 'expired', name='match_status'), nullable=False, server_default='pending'),
        sa.Column('provider_response', sa.Text(), nullable=True),
        sa.Column('provider_responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Connections
    op.create_table(
        'connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('request_matches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.Enum('pending', 'active', 'in_progress', 'completed', 'cancelled', name='connection_status'), nullable=False, server_default='pending'),
        sa.Column('connected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requester_confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider_confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Reviews
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewee_provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Provider Trust Scores
    op.create_table(
        'provider_trust_scores',
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('phone_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('identity_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('profile_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('rating_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('completion_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('recommendation_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('response_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('trust_score', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('calculation_version', sa.String(50), nullable=False, server_default='v2'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Recommendations (system)
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('requests.id', ondelete='CASCADE'), nullable=True),
        sa.Column('score', sa.Numeric(6, 2), nullable=False, server_default='0'),
        sa.Column('reason', postgresql.JSONB(), nullable=True),
        sa.Column('algorithm_version', sa.String(50), nullable=False, server_default='v1'),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Provider Recommendations (community)
    op.create_table(
        'provider_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recommender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('connections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Saved Providers
    op.create_table(
        'saved_providers',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('providers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Notifications
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Enum('new_match', 'provider_response', 'connection_request', 'connection_accepted', 'review_reminder', 'request_completed', 'system', name='notification_type'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('saved_providers')
    op.drop_table('provider_recommendations')
    op.drop_table('recommendations')
    op.drop_table('provider_trust_scores')
    op.drop_table('reviews')
    op.drop_table('connections')
    op.drop_table('request_matches')
    op.drop_table('requests')
    op.drop_table('provider_availability')
    op.drop_table('locations')
    op.drop_table('provider_services')
    op.drop_table('providers')
    op.drop_table('services')
    op.drop_table('categories')
    op.drop_table('profiles')
    op.execute("DROP TYPE IF EXISTS notification_type;")
    op.execute("DROP TYPE IF EXISTS connection_status;")
    op.execute("DROP TYPE IF EXISTS match_status;")
    op.execute("DROP TYPE IF EXISTS request_status;")
