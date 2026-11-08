from app.utils.otp import generate_otp

def test_generate_otp():
    otp = generate_otp()

    assert len(otp) == 6
    assert otp.isdigit()