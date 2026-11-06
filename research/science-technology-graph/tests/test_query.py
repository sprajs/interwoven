import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location("query",Path(__file__).parents[1]/"tools/query.py")
query=importlib.util.module_from_spec(spec);spec.loader.exec_module(query)
class QueryTests(unittest.TestCase):
 def test_commercial_question_is_independent_of_display_anchor(self):
  def node(id,kind,status,anchor):return {"id":id,"kind":kind,"lifecycle":{"first_commercial_availability":{"status":status}},"graph_anchor":{"status":anchor}}
  rows=[node("state-vessel","technology","unknown","selected"),node("product","technology","documented","selected"),node("unresearched","technology","not_yet_researched","not_yet_researched"),node("discovery","science","not_applicable","selected")]
  self.assertEqual([n["id"] for n in query.unresolved_commercial(rows)],["state-vessel","unresearched"])
if __name__=="__main__":unittest.main()
