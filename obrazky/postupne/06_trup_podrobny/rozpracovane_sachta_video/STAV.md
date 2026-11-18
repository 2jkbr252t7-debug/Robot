# Rozpracované (zastavené na pokyn používateľa 18. 11. 2026)

1. Kontrola pevnosti šachty (P_sachta: dno, prilepené mosadzné koleso, čap T_cap + PTFE, skrutka F15, okraj okolo
   kolesa, tenké rohy, podložky modulu zdvihu) – dve nezávislé kontroly boli rozbehnuté a zastavené pred záverom:
   * sachta_a/ – meranie hrúbok na skutočnom tvare (g02–g08), čap (h01), 3-D voxelový FE (fe3d.py, fe_cases*.py, logy
     fe_run1–4) – výsledky FE ešte neboli vyhodnotené, správa report.md nevznikla;
   * sachta_b/ – meranie a analýza previsov pri tlači (m01, m02), výpočty reálnych porúch (pád, pretiahnutie skrutky,
     tečenie, opotrebenie, teplo) neboli dokončené.
   Doterajší stav podľa kontroly K12 (všetky riadky prechádzajú) je v NAVRH_trup.md a zdroj/checks.json.
2. Video mechanizmov s komentárom – nezačaté (čakalo na voľný výkon). Animačný model s kĺbmi je hotový a overený
   (../mechanizmy/), interaktívna 3D stránka je zverejnená.

Pokračovanie: dokončiť obe kontroly šachty (report + slovenské zhrnutie, prípadné zosilnenie), potom vyrenderovať video
podľa scenára (otáčanie trupu zospodu, otočenie hlavy cez ozubenie, zdvih krku zboku cez kľuku, náklon hlavy, všetko naraz).
