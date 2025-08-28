from unittest.mock import Mock, patch

from src.ctrl_alt_heal.tools.identity_tool import (
    find_user_by_identity_tool,
    create_user_with_identity_tool,
    get_or_create_user_tool,
)
from src.ctrl_alt_heal.domain.models import User


@patch("src.ctrl_alt_heal.tools.identity_tool.IdentitiesStore")
@patch("src.ctrl_alt_heal.tools.identity_tool.UsersStore")
def test_find_user_by_identity_found(mock_users_store, mock_identities_store):
    # Mock setup
    mock_identities_instance = Mock()
    mock_users_instance = Mock()
    mock_identities_store.return_value = mock_identities_instance
    mock_users_store.return_value = mock_users_instance

    # Test data
    user_id = "test-user-123"
    user = User(
        user_id=user_id,
        first_name="John",
        last_name="Doe",
        username="johndoe",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )

    mock_identities_instance.find_user_id_by_identity.return_value = user_id
    mock_users_instance.get_user.return_value = user

    # Test
    result = find_user_by_identity_tool("telegram", "123456")

    # Assertions
    assert result["status"] == "found"
    assert result["user_id"] == user_id
    assert result["user"]["first_name"] == "John"
    mock_identities_instance.find_user_id_by_identity.assert_called_once_with(
        "telegram", "123456"
    )
    mock_users_instance.get_user.assert_called_once_with(user_id)


@patch("src.ctrl_alt_heal.tools.identity_tool.IdentitiesStore")
@patch("src.ctrl_alt_heal.tools.identity_tool.UsersStore")
def test_find_user_by_identity_not_found(mock_users_store, mock_identities_store):
    # Mock setup
    mock_identities_instance = Mock()
    mock_identities_store.return_value = mock_identities_instance

    mock_identities_instance.find_user_id_by_identity.return_value = None

    # Test
    result = find_user_by_identity_tool("telegram", "123456")

    # Assertions
    assert result["status"] == "not_found"
    assert "No user found" in result["message"]


@patch("src.ctrl_alt_heal.tools.identity_tool.IdentitiesStore")
@patch("src.ctrl_alt_heal.tools.identity_tool.UsersStore")
@patch("src.ctrl_alt_heal.tools.identity_tool.datetime")
def test_create_user_with_identity_success(
    mock_datetime, mock_users_store, mock_identities_store
):
    # Mock setup
    mock_identities_instance = Mock()
    mock_users_instance = Mock()
    mock_identities_store.return_value = mock_identities_instance
    mock_users_store.return_value = mock_users_instance

    mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

    # User doesn't exist yet
    mock_identities_instance.find_user_id_by_identity.return_value = None

    # Mock user creation - the upsert_user method will set the user_id
    mock_users_instance.upsert_user.side_effect = lambda user: setattr(
        user, "user_id", "test-user-123"
    )

    # Test
    result = create_user_with_identity_tool(
        "telegram", "789012", "Jane", "Smith", "janesmith"
    )

    # Assertions
    assert result["status"] == "created"
    assert result["user_id"] == "test-user-123"
    assert "Created new user" in result["message"]
    mock_users_instance.upsert_user.assert_called_once()
    mock_identities_instance.link_identity.assert_called_once()


@patch("src.ctrl_alt_heal.tools.identity_tool.find_user_by_identity_tool")
@patch("src.ctrl_alt_heal.tools.identity_tool.create_user_with_identity_tool")
def test_get_or_create_user_existing(mock_create, mock_find):
    # Mock existing user found
    mock_find.return_value = {
        "status": "found",
        "user_id": "existing-user-123",
        "user": {"first_name": "Existing", "last_name": "User"},
    }

    # Test
    result = get_or_create_user_tool("telegram", "123456", "New", "User", "newuser")

    # Assertions
    assert result["status"] == "existing_user"
    assert result["user_id"] == "existing-user-123"
    mock_find.assert_called_once_with("telegram", "123456")
    mock_create.assert_not_called()


@patch("src.ctrl_alt_heal.tools.identity_tool.find_user_by_identity_tool")
@patch("src.ctrl_alt_heal.tools.identity_tool.create_user_with_identity_tool")
def test_get_or_create_user_new(mock_create, mock_find):
    # Mock no existing user found
    mock_find.return_value = {"status": "not_found"}

    # Mock user creation
    mock_create.return_value = {
        "status": "created",
        "user_id": "new-user-123",
        "user": {"first_name": "New", "last_name": "User"},
    }

    # Test
    result = get_or_create_user_tool("telegram", "123456", "New", "User", "newuser")

    # Assertions
    assert result["status"] == "new_user"
    assert result["user_id"] == "new-user-123"
    mock_find.assert_called_once_with("telegram", "123456")
    mock_create.assert_called_once_with("telegram", "123456", "New", "User", "newuser")
