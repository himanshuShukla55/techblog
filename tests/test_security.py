from techblog.utilities.security import hash_password, verify_password


def test_plaintext_differs_from_hash():
    password = "password"

    hashed_password = hash_password(password)

    assert password != hashed_password


def test_correct_password_verifies():
    password = "password"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password)


def test_incorrect_password_fails():
    password = "password"
    incorrect_password = "incorrect_password"
    hashed_password = hash_password(password)

    assert not verify_password(incorrect_password, hashed_password)


def test_same_password_produces_different_hashes():
    password = "password"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)
