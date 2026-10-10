"""Render report.md as six-page A4/11pt PDF; optional authoring dependencies only.

Usage: python docs/report/build_pdf.py --font-dir /path/to/dejavu
Requires reportlab, Pillow and pypdf (not part of scientific reproduction).
"""
from pathlib import Path
import argparse
import html
import re
from urllib.parse import quote
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from pypdf import PdfReader


def render(font_dir: Path) -> Path:
    """Use source text, fixed metadata, explicit page groups and embedded Unicode fonts."""
    folder=Path(__file__).resolve().parent;root=folder.parent.parent
    pdfmetrics.registerFont(TTFont('Body',str(font_dir/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('BodyBold',str(font_dir/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold')
    ink=colors.HexColor('#173451');accent=colors.HexColor('#B35335')
    body=ParagraphStyle('body',fontName='Body',fontSize=11,leading=13,spaceAfter=5,textColor=colors.HexColor('#27313B'))
    head=ParagraphStyle('heading',parent=body,fontName='BodyBold',fontSize=14,leading=17,spaceBefore=4,spaceAfter=8,textColor=ink)
    small=ParagraphStyle('small',parent=body,fontSize=8,leading=10,spaceAfter=4)
    cell=ParagraphStyle('cell',parent=body,fontSize=9,leading=11,spaceAfter=0)
    title=ParagraphStyle('title',parent=head,fontSize=18,leading=22,spaceAfter=6)
    story=[]

    def inline(text):
        text=text.replace('–','-').replace('—','-').replace('‑','-')
        text=re.sub(r'\{\{(.*?)\}\}',lambda m:'[Pending: '+m.group(1)+']',text)
        text=html.escape(text)
        text=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)
        text=re.sub(r'`(.*?)`',r'\1',text)
        def link(match):
            label,url=match.groups()
            if not url.startswith(('https://','http://')):
                path=(folder/url).resolve()
                url='https://github.com/mpssriram/speech-eval/blob/main/'+quote(path.relative_to(root).as_posix())
            return f'<link href="{url}" color="#326B89">{label}</link>'
        return re.sub(r'\[([^\[\]]+)\]\(([^)]+)\)',link,text)

    def paragraph(text,style=body):return Paragraph(inline(text),style)
    story += [paragraph('Speech-Eval',title),paragraph('Contrastive Speech Delivery Analytics with Temporal Flaw Grounding',head),
              paragraph('Multimodal AI Hackathon 2026 - Track C | October 2026',small),
              paragraph('Author pending confirmation; with Claude and Codex. Genuine user takes and independent ratings pending.',small),
              Spacer(1,8)]
    text=(folder/'report.md').read_text(encoding='utf-8')
    text=re.sub(r'^---\n.*?\n---\n','',text,flags=re.S)
    lines=text.splitlines();i=0;page5=False
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('# '):
            if line.startswith(('# 3.','# 5.','# 6.','# 7.')):story.append(PageBreak())
            story.append(paragraph(line[2:],head));i+=1;continue
        if line.startswith('|'):
            table=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[s.strip() for s in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-:]+',s) for s in row):table.append([paragraph(s,cell) for s in row])
                i+=1
            n=len(table[0]);width=A4[0]-112
            fractions={3:[.25,.39,.36],4:[.24,.32,.27,.17],6:[.21,.08,.12,.12,.31,.16]}.get(n,[1/n]*n)
            visual=Table(table,colWidths=[width*f for f in fractions],repeatRows=1,hAlign='LEFT')
            visual.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF0F3')),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F7F8F9')]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),
                ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),3),
                ('BOTTOMPADDING',(0,0),(-1,-1),3),('LINEBELOW',(0,0),(-1,0),1,ink)]))
            story.extend([visual,Spacer(1,9)]);continue
        if line.startswith('$$'):
            equation=line
            while not equation.endswith('$$') or equation=='$$':
                i+=1;equation+=' '+lines[i].strip()
            if 'mathrm{st}' in equation:
                plain='st(t) = 12 log₂[f₀(t) / median f₀]; Lrel(t) = L(t) - median L.'
            else:plain='σ²ᵢ,𝒇 = (n s²ᵢ,𝒇 + n₀ σ²pool,𝒇) / (n + n₀); zⱼ,𝒇 = (xⱼ,𝒇 - μᵢ,𝒇) / σᵢ,𝒇.'
            # Use conventional plain-text subscripts that the embedded font supports.
            plain=plain.replace('𝒇','f')
            story.append(paragraph(plain));i+=1;continue
        if line.startswith('!['):
            match=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
            image=Image(str((folder/match.group(2)).resolve()))
            scale=min((A4[0]-112)/image.imageWidth,300/image.imageHeight)
            image.drawWidth=image.imageWidth*scale;image.drawHeight=image.imageHeight*scale
            story.extend([image,paragraph(match.group(1),small)]);i+=1;continue
        chunk=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','$$','![')):
            chunk.append(lines[i].strip());i+=1
        joined=' '.join(chunk)
        if joined.startswith('C uses **different eligibility') and not page5:
            story.extend([PageBreak(),paragraph('6. Results - no-reference comparison',head)]);page5=True
        story.append(paragraph(joined))

    def footer(canvas,doc):
        canvas.setStrokeColor(accent);canvas.line(56,40,A4[0]-56,40)
        canvas.setFont('Body',8);canvas.setFillColor(ink)
        canvas.drawString(56,27,'Frozen synthetic benchmark - human evidence pending')
        canvas.drawRightString(A4[0]-56,27,str(doc.page))
    output=folder/'report.pdf'
    doc=SimpleDocTemplate(str(output),pagesize=A4,invariant=1,leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=55,
        title='Speech-Eval: Contrastive Speech Delivery Analytics',author='Author pending; Claude and Codex assistance')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    count=len(PdfReader(output).pages)
    if count!=6:raise ValueError(f'Six-page budget not met: {count} pages')
    print(f'Six A4 pages created: {output}')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font-dir',type=Path,required=True)
    render(parser.parse_args().font_dir)
