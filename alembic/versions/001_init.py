"""001 init — base tables"""
revision = "001_init"
down_revision = None
branch_labels = None
depends_on = None
def upgrade(): pass  # Base.metadata.create_all handles v0; kept for history
def downgrade(): pass
