import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from subset_legacy_fonts import parse,used_chars,NAMES,SOURCE,subset
class LegacyFontSubsets(unittest.TestCase):
 def test_every_kept_glyph_retains_original_metrics_and_bitmap_bytes(self):
  for name in NAMES:
   old=parse((SOURCE/(name+'.c')).read_text('utf-8'))
   new=parse((ROOT/'firmware/main'/(name+'.c')).read_text('utf-8'))
   self.assertEqual(set(new),used_chars()|{None})
   for char,item in new.items():self.assertEqual(item,old[char],(name,char))
 def test_subset_reproduces_checked_in_font_and_removes_only_unused_glyphs(self):
  for name in NAMES:
   old=(SOURCE/(name+'.c')).read_text('utf-8');result,size,count=subset(old,used_chars())
   self.assertEqual((ROOT/'firmware/main'/(name+'.c')).read_text('utf-8'),'/* Lossless used-glyph subset; regenerate with tools/subset_legacy_fonts.py. */\n'+result)
   self.assertLess(count,160);self.assertLess(size,14000)
 def test_missing_source_glyph_is_rejected(self):
  with self.assertRaisesRegex(ValueError,'lacks'):subset((SOURCE/'nabo_ui_font_18.c').read_text('utf-8'),{'\U0001f680'})
