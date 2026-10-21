"""Create a technical PDF and standalone scientific plots from recorded results."""
import argparse, json, pathlib, sys
from xml.sax.saxutils import escape

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--deps');args=parser.parse_args()
if args.deps:sys.path.insert(0,args.deps)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=pathlib.Path(__file__).resolve().parent
A=json.loads((ROOT/'results'/'analysis.json').read_text(encoding='utf-8'))
if not A['complete']:raise SystemExit('Refusing a final report: run is not complete')
DATA=json.loads((ROOT/'data'/'cases.json').read_text(encoding='utf-8'))
manifest=json.loads((ROOT/'runs'/'predictions.manifest.json').read_text(encoding='utf-8'))
protocol=json.loads((ROOT/'protocol.json').read_text(encoding='utf-8'))
OUT=ROOT/'reports';OUT.mkdir(exist_ok=True)
(ROOT/'requirements-report.txt').write_text(f'matplotlib=={matplotlib.__version__}\nreportlab=={reportlab.Version}\n',encoding='utf-8')
FONT='Helvetica';BOLD='Helvetica-Bold'
if pathlib.Path('C:/Windows/Fonts/arial.ttf').exists():
    pdfmetrics.registerFont(TTFont('LabArial','C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('LabArialBold','C:/Windows/Fonts/arialbd.ttf'))
    FONT='LabArial';BOLD='LabArialBold'
INK=colors.HexColor('#19312e');GREEN=colors.HexColor('#156e59');MUTED=colors.HexColor('#536861')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle('TitleLab',fontName=BOLD,fontSize=28,leading=31,textColor=INK,spaceAfter=14))
styles.add(ParagraphStyle('SubLab',fontName=FONT,fontSize=12,leading=17,textColor=MUTED,spaceAfter=14))
styles.add(ParagraphStyle('HeadingLab',fontName=BOLD,fontSize=15,leading=19,textColor=GREEN,spaceBefore=12,spaceAfter=8))
styles.add(ParagraphStyle('BodyLab',fontName=FONT,fontSize=9.5,leading=14,textColor=INK,spaceAfter=8))
styles.add(ParagraphStyle('SmallLab',fontName=FONT,fontSize=7.8,leading=11,textColor=MUTED,spaceAfter=7))
styles.add(ParagraphStyle('CellLab',fontName=FONT,fontSize=8,leading=10,textColor=INK))
def P(text,style='BodyLab'):return Paragraph(text,styles[style])
def pct(v):return '-' if v is None else f'{100*v:.1f}'
def short(m):return {'qwen2.5:1.5b':'Qwen2.5 1.5B','qwen3:8b':'Qwen3 8B','rule_extractor':'Rule extractor','always_abstain':'Always abstain'}[m]
def get(track='controlled_technical',split='heldout',gate='raw',baselines=False):
    return [s for s in A['summaries'] if s['track']==track and s['split']==split and s['gate']==gate and (baselines or s['strategy']!='baseline')]
def table(rows,widths):
    cells=[[P(escape(str(v)),'CellLab') for v in row] for row in rows]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eee7')),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),7),
        ('LINEBELOW',(0,0),(-1,0),.7,GREEN),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d7e1d9'))]))
    return t

# Standard plotting: clustered uncertainty, paired variants, no decorative scores.
main=get();fig,ax=plt.subplots(figsize=(7.1,3.1))
plt.rcParams.update({'font.size':9,'font.family':'DejaVu Sans'})
labels=[]
for i,s in enumerate(main):
    val=s['balanced_accuracy'];lo,hi=s['balanced_ci95'];color='#156e59' if '1.5b' in s['model'] else '#436caa'
    ax.errorbar(100*val,i,xerr=[[100*(val-lo)],[100*(hi-val)]],fmt='o',color=color,capsize=4)
    labels.append(short(s['model'])+' / '+s['strategy'])
ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis();ax.set_xlim(0,103)
ax.axvline(50,color='#9c9c91',linestyle='--',linewidth=1,label='Always abstain: 50%')
ax.axvline(100,color='#c2c8bd',linestyle=':',linewidth=1,label='Rule extractor: 100%')
ax.set_xlabel('Balanced accuracy (%) - held-out controlled track');ax.grid(axis='x',alpha=.18)
ax.spines[['top','right']].set_visible(False);fig.tight_layout()
fig.savefig(OUT/'balanced-accuracy.png',dpi=200);fig.savefig(OUT/'balanced-accuracy.svg');plt.close(fig)

story=[]
story += [P('VietEvidence Lab','TitleLab'),P('Evidence-grounded Vietnamese technical assistants<br/>A reproducible local-model feasibility study','SubLab'),
          P('Version 1.0 | 21 October 2026 | AI-assisted student project','SmallLab'),
          P('Project owner: Nguyễn Ngọc Minh. Student affiliation is self-reported; this work does not imply university or laboratory endorsement.','SmallLab'),
          P('Research question','HeadingLab'),
          P('How do support-checking instructions and a literal-citation gate change answer accuracy and abstention when a Vietnamese document omits a fact, contains another revision, or includes an instruction that tries to override the reading task?'),
          P('Initial findings','HeadingLab'),
          P('Stronger support-checking prompts did not consistently improve held-out balanced accuracy. The literal gate improved scores for the smaller model but left residual unsupported answers; a task-specific rule extractor solved the narrow generated layouts. These observations motivate broader data and independent review, rather than a general effectiveness claim.'),
          P('What was actually executed','HeadingLab'),
          table([['Component','Recorded scope'],['Controlled technical track','24 fictional device dossiers x 4 conditions = 96 cases. 8 development and 16 held-out dossiers.'],['Natural-text exploratory track','20 curated XQuAD question/passage pairs x 2 conditions = 40 cases. 10 pairs in each split.'],['Model inference','2 local model snapshots x 3 fixed prompts x 136 cases = 816 recorded requests. No Google-model runs.'],['Additional analyses','Offline citation gate, always-abstain and task-specific rule baselines; 2,000 cluster bootstrap samples.']],[145,360]),
          P('Design and controls','HeadingLab'),
          P('The protocol, data and prompts were hashed before the main run. All variants of a dossier or question remain in one split. Independent requests use temperature 0, a fixed seed, a 4,096-token context, a 256-output-token cap, and thinking disabled. All strategies share a structured JSON answer/citation schema and a common document-trust boundary; they differ in support instructions.'),
          P('Primary outcomes are answerable exact match (EM), unsupported-answer rate on missing cases, and balanced accuracy: the mean of answerable EM and correct abstention. Malformed or failed responses receive zero task correctness and remain in the denominator.'),
          P('Interpretation boundary','HeadingLab'),
          P('This is a completed pilot execution, not independently validated scientific efficacy. Technical facts are generated fiction, natural negative labels remain provisional, and the student has not yet independently reproduced the full study. No field measurements, publication, or production deployment are claimed.'),PageBreak()]

story += [P('1 / Controlled technical results','TitleLab'),
          P('Held-out set: 16 dossiers, 64 cases per configuration; 48 answerable and 16 missing. Values below are percentages.','SmallLab')]
rows=[['Model / prompt','EM','Unsupported','False refuse','Invalid','Balanced [95% CI]']]
for s in main:
    lo,hi=s['balanced_ci95'];rows.append([short(s['model'])+' / '+s['strategy'],pct(s['em']),pct(s['unsupported_rate']),pct(s['false_abstention_rate']),pct(s['failure_rate']),f"{pct(s['balanced_accuracy'])} [{pct(lo)}, {pct(hi)}]"])
story += [table(rows,[140,46,70,65,44,140]),Spacer(1,12),Image(str(OUT/'balanced-accuracy.png'),width=505,height=220),
          P('Error bars are descriptive percentile intervals resampled by whole dossier. With 16 held-out dossiers, intervals can be unstable or degenerate on simple templates; they are not corrected significance tests. The task-specific rule extractor achieves 100% here, demonstrating that these templates are solvable without a language model. Always abstaining scores 50% balanced accuracy.','SmallLab'),
          P('Predefined paired comparisons','HeadingLab')]
comp=[['Model','Comparison','Balanced delta, points [95% CI]']]
for c in A['comparisons']:
    if c['track']=='controlled_technical' and c['split']=='heldout' and c['comparison'] in ('cite minus direct','verify minus direct'):
        comp.append([short(c['model']),c['comparison'],f"{100*c['delta']:+.1f} [{100*c['ci95'][0]:+.1f}, {100*c['ci95'][1]:+.1f}]"])
story += [table(comp,[140,150,215]),P('A comparison interval that spans zero does not establish an improvement in this pilot. Do not select a prompt on the held-out results and then present the same set as a fresh confirmatory test.','SmallLab'),PageBreak()]

story += [P('2 / Filtering and transfer checks','TitleLab'),P('Literal citation gate','HeadingLab'),
          P('The offline gate retains an answer only when its normalized evidence occurs in the supplied document and contains the answer. Otherwise it abstains. This can remove unsupported output, reject correct paraphrases, or retain a quote about the wrong target; it does not prove entailment. No extra model inference is counted for the gate.')]
rows=[['Model / prompt','Raw balanced','Gated balanced','Raw coverage','Gated coverage']]
for s in main:
    g=next(x for x in get(gate='literal_gate') if x['model']==s['model'] and x['strategy']==s['strategy'])
    rows.append([short(s['model'])+' / '+s['strategy'],pct(s['balanced_accuracy']),pct(g['balanced_accuracy']),pct(s['coverage']),pct(g['coverage'])])
story += [table(rows,[165,85,85,85,85]),P('Coverage is the fraction of all cases that receive an answer. Always read a reduction in unsupported answers alongside lost answer coverage and unnecessary abstention. Full error and condition counts are in results/analysis.json.','SmallLab'),
          P('XQuAD: exploratory natural-text branch','HeadingLab'),
          P('Held-out set: 10 pairs, 20 cases per configuration. Negative variants were formed by deleting answer-containing sentences. Their unanswerability has not been independently verified; the following values are provisional and kept separate from controlled results.','SmallLab')]
rows=[['Model / prompt','EM','Token F1','Unsupported','Invalid','Balanced']]
for s in get(track='xquad_exploratory'):
    rows.append([short(s['model'])+' / '+s['strategy'],pct(s['em']),pct(s['f1']),pct(s['unsupported_rate']),pct(s['failure_rate']),pct(s['balanced_accuracy'])])
story += [table(rows,[165,60,70,80,60,70]),
          P('Natural-text transfer cannot be inferred from a high technical-template score. XQuAD is public and may have been seen during training; lexical EM/F1 can miss valid paraphrases, and deleting an answer span can leave indirect evidence.','SmallLab'),
          P('Failure accounting','HeadingLab')]
raw=json.loads('['+','.join((ROOT/'runs'/'predictions.jsonl').read_text(encoding='utf-8').splitlines())+']')
fail=sum(r['parsed'] is None for r in raw);truncated=sum(bool(r['raw'] and r['raw'].get('done_reason')=='length') for r in raw)
story += [P(f'All 816 requests were retained: {fail} invalid/failed responses and {truncated} outputs with a length stop. These counts describe recorded outputs, not discarded trials. Transport errors, parse errors and the full generated text remain in the run file. Latency is a single-machine observation affected by cache, load, and power state; it is not a deployment guarantee.'),PageBreak()]

story += [P('3 / Reproducibility and next study','TitleLab'),P('Provenance','HeadingLab')]
modeltexts=[]
for m in manifest['models']:
    modeltexts.append(f"{escape(m['name'])}: {escape(m['details'].get('quantization_level','unknown'))}, digest {m['digest'][:16]}...")
story += [P('<br/>'.join(modeltexts),'SmallLab'),
          P('Runtime: Ollama '+escape(manifest['ollama']['version'])+'. Hardware recorded separately in runs/environment.json. Full digests, versions and request settings are in runs/predictions.manifest.json.','SmallLab'),
          P('Dataset SHA-256 (canonical JSON): '+A['dataset_hash'],'SmallLab'),
          P('To verify: run the unit tests, rebuild the dataset and compare its frozen hash, then rerun analysis against the supplied raw JSONL. To reproduce generation, use a separate project copy with the same model digests and runtime. Greedy seeded GPU execution does not guarantee bit-for-bit repeatability across platforms.'),
          P('Limits that matter','HeadingLab'),
          P('The controlled set has narrow, partially shared templates; synthetic records are not hardware measurements or evidence of safe engineering decisions. Independent label review is absent. One seeded response per setting does not quantify generation variability. The two model generations differ in architecture, training and size, so the study cannot isolate a parameter-count effect. There are only two closely related Qwen models; cloud-model and wider-family generalization remain untested.'),
          P('Feasible 6-12 month work plan','HeadingLab'),
          table([['Period','Concrete next output'],['Month 1','Student reproduction, semantic label review and an openly logged error audit; seek independent feedback.'],['Months 2-3','Legally reusable Vietnamese technical manuals, more question types, and a new held-out test set.'],['Months 4-6','Retrieval/context errors, additional model families and attack types, repeated runs and actual resource measurements.'],['Months 7-12','Reviewed data/code/report release; external replication and publication only if evidence and contribution justify it.']],[85,420]),
          P('Antigravity would support experiment adapters, automated checks, experiment manifests and error analysis as the project expands. No Antigravity-produced result is claimed here, and upgraded IDE usage is not assumed to include unrelated model API credits.','SmallLab'),
          P('Research integrity and sources','HeadingLab'),
          P('Implementation, dataset preparation, execution and this initial analysis were AI-assisted. No human review signatures were fabricated; the review worksheet is blank. No academic paper, advisor or laboratory affiliation is claimed. This pilot is not endorsed by HUST, Google or dataset/model authors.','SmallLab'),
          P('[1] XQuAD, Artetxe, Ruder and Yogatama: github.com/google-deepmind/xquad (pinned source commit in data metadata). CC BY-SA 4.0 derivatives.<br/>[2] Tran et al. (2023), Revealing Weaknesses of Vietnamese Language Models Through Unanswerable Questions: aclanthology.org/2023.eacl-srw.1/<br/>[3] Asai et al. (2023), Self-RAG: arxiv.org/abs/2310.11511. This pilot does not implement Self-RAG training or retrieval.<br/>[4] Model/runtime documentation and licenses: ATTRIBUTION.md. Original code MIT; synthetic records CC BY 4.0; model weights not redistributed.','SmallLab')]

def footer(canvas,doc):
    canvas.saveState();w,h=A4;canvas.setStrokeColor(colors.HexColor('#d7e1d9'));canvas.line(45,38,w-45,38)
    canvas.setFont(FONT,8);canvas.setFillColor(MUTED);canvas.drawString(45,25,'VietEvidence Lab | Reproducible pilot | 21 October 2026');canvas.drawRightString(w-45,25,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(OUT/'vietevidence-report.pdf'),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=39,bottomMargin=51,title='VietEvidence Lab - Reproducible Pilot',author='VietEvidence Lab contributors; AI-assisted')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(json.dumps({'pdf':str(OUT/'vietevidence-report.pdf'),'invalid_outputs':fail,'length_stops':truncated}))
