import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from engine import eligibility, notice, assistant


def status(profile, sid):
    return next(r["status"] for r in eligibility.evaluate(profile)["results"] if r["id"] == sid)


class T(unittest.TestCase):
    def test_kisan_eligible(self):
        self.assertEqual(status({"owns_land": "yes", "it_payer": "no", "govt_employee": "no"}, "pm-kisan"), "eligible")

    def test_kisan_tax_payer_rejected(self):
        self.assertEqual(status({"owns_land": "yes", "it_payer": "yes", "govt_employee": "no"}, "pm-kisan"), "not_eligible")

    def test_unknown_is_maybe(self):
        self.assertEqual(status({"age": 30}, "apy"), "maybe")

    def test_age_boundary(self):
        self.assertEqual(status({"age": 41, "bank_account": "yes", "it_payer": "no"}, "apy"), "not_eligible")
        self.assertEqual(status({"age": 40, "bank_account": "yes", "it_payer": "no"}, "apy"), "eligible")

    def test_any_rule(self):
        self.assertEqual(status({"age": 72}, "pm-jay"), "eligible")
        self.assertEqual(status({"age": 30, "bpl": "no", "income": 900000}, "pm-jay"), "not_eligible")

    def test_scholarship(self):
        p = {"category": "SC", "occupation": "student", "income": 200000}
        self.assertEqual(status(p, "post-matric-sc"), "eligible")

    def test_retrieval_multilingual(self):
        self.assertEqual(assistant.ask("मुझे पेंशन चाहिए", "hi")["sources"][0]["id"] in ("apy", "ignoaps"), True)
        self.assertEqual(assistant.ask("scholarship for college fees")["sources"][0]["id"], "post-matric-sc")

    def test_notice(self):
        a = notice.analyse("Applicants must submit the form before 15/12/2026 with Aadhaar. A fee of Rs. 500 shall be paid. "
                           "Last date for submission is 15/12/2026.")
        self.assertIn("15/12/2026", a["dates"])
        self.assertTrue(any("500" in m for m in a["amounts"]))
        self.assertIn("aadhaar", a["documents"])

    def test_all_languages_localised(self):
        for lang in ("hi", "kn", "ta", "te"):
            res = eligibility.evaluate({"age": 65, "bpl": "yes"}, lang=lang)["results"]
            for r in res:
                self.assertNotEqual(r["name"], next(x["name"] for x in eligibility.load_schemes() if x["id"] == r["id"]), lang)
            ans = assistant.ask("farmer help", lang)["answer"]
            self.assertFalse(ans.isascii(), lang)


if __name__ == "__main__":
    unittest.main()
