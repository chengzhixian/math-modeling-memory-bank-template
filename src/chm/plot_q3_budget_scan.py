"""Plot the reproducible conditional budget scan without extra plotting dependencies."""
import csv,math,argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',default='q3_b7_numerical_audit_v2')
    parser.add_argument('--output',default='q3_budget_scan.png')
    args=parser.parse_args()
    rows=list(csv.DictReader((ROOT/'outputs/chm'/args.source/'budget_scan.csv').open()))
    rows=[r for r in rows if r['context_tokens']=='8192' and r['feasible']=='True']
    im=Image.new('RGB',(1800,800),'white');d=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',27)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23)
    colors={'exponential':'#0072B2','power':'#D55E00','logarithmic':'#009E73'}
    d.text((80,25),'B7 conditional budget allocation | context = 8192 | Q0 = 0.5',fill='#222222',font=font)
    for panel,(field,label,lo,hi) in enumerate((('Q_score','Native quality Q',.48,1.02),('B7_diagnostic_loss','B7 diagnostic loss',1.9,3.4))):
        x0=110+panel*880;y0=110;w=700;h=530
        def xy(r):return (x0+w*(math.log10(float(r['budget_FLOPs']))-19)/5,y0+h*(hi-float(r[field]))/(hi-lo))
        d.text((x0,y0-45),label,fill='#222222',font=font)
        for i in range(6):
            x=x0+w*i/5
            d.line((x,y0,x,y0+h),fill='#dddddd',width=2)
            d.text((x-23,y0+h+15),str(19+i),fill='#444444',font=small)
        for i in range(5):
            y=y0+h*i/4;v=hi-(hi-lo)*i/4
            d.line((x0,y,x0+w,y),fill='#dddddd',width=2)
            d.text((x0-75,y-12),f'{v:.2f}',fill='#444444',font=small)
        for family,color in colors.items():
            points=[xy(r) for r in rows if r['quality_family']==family]
            d.line(points,fill=color,width=5)
        d.text((x0+220,y0+h+52),'log10 budget / FLOPs',fill='#222222',font=small)
    for i,(name,color) in enumerate(colors.items()):
        x=280+i*440;d.line((x,754,x+50,754),fill=color,width=6)
        d.text((x+65,738),name,fill='#222222',font=font)
    im.save(ROOT/'paper/latex/figures/chm'/args.output)

if __name__=='__main__':main()
