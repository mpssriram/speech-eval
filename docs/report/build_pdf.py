"""Render report.md as a compact A4/11pt PDF; optional authoring dependencies only.

Usage: python docs/report/build_pdf.py --font-dir /path/to/dejavu
Requires reportlab, Pillow and pypdf (not part of scientific reproduction).
"""
from pathlib import Path
import argparse
import html
import re
from urllib.parse import quote
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether,Flowable
from pypdf import PdfReader


class ScreenshotExcerpt(Flowable):
    """Lay out a viewport of the original screenshot without rewriting its pixels."""
    def __init__(self,path: Path,width: float,top_px: int,bottom_px: int):
        from PIL import Image as PILImage
        super().__init__()
        self.path=path
        self.source_width,self.source_height=PILImage.open(path).size
        self.width=width;self.scale=width/self.source_width
        self.top_px=top_px;self.bottom_px=bottom_px
        self.height=(bottom_px-top_px)*self.scale

    def draw(self):
        self.canv.saveState()
        clip=self.canv.beginPath();clip.rect(0,0,self.width,self.height)
        self.canv.clipPath(clip,stroke=0,fill=0)
        self.canv.drawImage(str(self.path),0,-(self.source_height-self.bottom_px)*self.scale,
            width=self.width,height=self.source_height*self.scale)
        self.canv.restoreState()


def render(font_dir: Path) -> Path:
    """Use source text, fixed metadata, natural pagination and embedded Unicode fonts."""
    folder=Path(__file__).resolve().parent;root=folder.parent.parent
    pdfmetrics.registerFont(TTFont('Body',str(font_dir/'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('BodyBold',str(font_dir/'DejaVuSans-Bold.ttf')))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='Body',boldItalic='BodyBold')
    ink=colors.HexColor('#173451');accent=colors.HexColor('#B35335')
    body=ParagraphStyle('body',fontName='Body',fontSize=11,leading=13,spaceAfter=5,textColor=colors.HexColor('#27313B'))
    head=ParagraphStyle('heading',parent=body,fontName='BodyBold',fontSize=14,leading=17,spaceBefore=8,spaceAfter=8,textColor=ink,keepWithNext=True)
    small=ParagraphStyle('small',parent=body,fontSize=8,leading=10,spaceAfter=4)
    cell=ParagraphStyle('cell',parent=body,fontSize=9,leading=11,spaceAfter=0)
    title=ParagraphStyle('title',parent=head,fontSize=18,leading=22,spaceAfter=6)
    quote_style=ParagraphStyle('quote',parent=body,leftIndent=12,rightIndent=8,textColor=ink)
    story=[]

    def inline(text):
        if '{{' in text or '[Pending:' in text:
            raise ValueError('Move unresolved placeholders to the final Pending items box')
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
              Spacer(1,8)]
    text=(folder/'report.md').read_text(encoding='utf-8')
    text=re.sub(r'^---\n.*?\n---\n','',text,flags=re.S)
    lines=text.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('::: '):
            kind=line[4:];i+=1;box=[]
            while i<len(lines) and lines[i].strip()!=':::':
                if lines[i].strip():box.append(paragraph(lines[i].strip(),cell if kind=='summary' else body))
                i+=1
            if i==len(lines):raise ValueError('Unclosed report box')
            visual=Table([[box]],colWidths=[A4[0]-112])
            visual.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#EAF0F3')),
                ('BOX',(0,0),(-1,-1),.7,ink),('LEFTPADDING',(0,0),(-1,-1),10),
                ('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),
                ('BOTTOMPADDING',(0,0),(-1,-1),8)]))
            story.extend([visual,Spacer(1,9)]);i+=1;continue
        if line.startswith('# '):
            story.append(paragraph(line[2:],head));i+=1;continue
        if line.startswith('> '):
            story.append(paragraph(line[2:],quote_style));i+=1;continue
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
            path=(folder/match.group(2)).resolve()
            viewport={'ui_results.png':(180,780)}.get(path.name)
            if viewport:image=ScreenshotExcerpt(path,A4[0]-112,*viewport)
            else:
                image=Image(str(path))
                max_height=120 if path.name=='ui_region.png' else 240
                scale=min((A4[0]-112)/image.imageWidth,max_height/image.imageHeight)
                image.drawWidth=image.imageWidth*scale;image.drawHeight=image.imageHeight*scale
            caption=f'[{match.group(1)}'+(' (excerpt; full screenshot)' if viewport else '')+f']({match.group(2)})'
            story.append(KeepTogether([image,paragraph(caption,small)]));i+=1;continue
        chunk=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','$$','![',':::','> ')):
            chunk.append(lines[i].strip());i+=1
        joined=' '.join(chunk)
        story.append(paragraph(joined))

    def footer(canvas,doc):
        canvas.setStrokeColor(accent);canvas.line(56,40,A4[0]-56,40)
        canvas.setFont('Body',8);canvas.setFillColor(ink)
        canvas.drawString(56,27,'Frozen synthetic benchmark')
        canvas.drawRightString(A4[0]-56,27,str(doc.page))
    output=folder/'report.pdf'
    doc=SimpleDocTemplate(str(output),pagesize=A4,invariant=1,leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=55,
        title='Speech-Eval: Contrastive Speech Delivery Analytics',author='Author pending; Claude and Codex assistance')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    count=len(PdfReader(output).pages)
    if count>6:raise ValueError(f'Six-page budget exceeded: {count} pages')
    print(f'{count} compact A4 pages created: {output}')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font-dir',type=Path,required=True)
    render(parser.parse_args().font_dir)
