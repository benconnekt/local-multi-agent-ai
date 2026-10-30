import Link from 'next/link';
export default function AudioVideoStudio() {
  return <main style={{maxWidth:880,margin:'0 auto',padding:'60px 24px'}}>
    <p style={{fontSize:12,letterSpacing:2,color:'#81d3b5'}}>FUTURE STUDIO</p>
    <h1>Audio-to-Video Studio</h1>
    <p style={{fontSize:16,color:'#b3c4d5',lineHeight:1.7}}>Coming soon. This dedicated workspace will support a future audio-to-video generation workflow. No media generation, uploads, processing jobs or background tasks are implemented yet.</p>
    <div style={{border:'1px solid #273648',borderRadius:12,padding:24,background:'#141f2d',marginTop:26}}><h2>Planned capabilities</h2><p style={{color:'#b3c4d5',lineHeight:1.7}}>Audio ingestion, transcript and scene planning, storyboard review, video generation, timeline editing and export. These are planned features, not active controls.</p></div>
    <p style={{marginTop:28}}><Link href="/" style={{color:'#81d3b5'}}>Return to Engineering Studio</Link></p>
  </main>;
}
