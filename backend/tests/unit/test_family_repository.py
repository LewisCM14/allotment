from unittest.mock import MagicMock

from app.api.repositories.family import family_repository


def test_family_repository_methods():
    mock_db = MagicMock()
    repo = family_repository.FamilyRepository(db=mock_db)
    assert hasattr(repo, "get_family_by_id")
    assert hasattr(repo, "add_family")
