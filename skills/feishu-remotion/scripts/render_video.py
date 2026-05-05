#!/usr/bin/env python3
import json
import os
import subprocess
import shutil
from pathlib import Path


def render_video(script, screenshots_dir, output_path):
    project_dir = create_remotion_project(script, screenshots_dir)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        'npx', 'remotion', 'render',
        str(project_dir / 'src' / 'index.tsx'),
        'MeetingSummary',
        str(output_path)
    ]
    
    env = os.environ.copy()
    env['NODE_ENV'] = 'production'
    
    result = subprocess.run(
        cmd,
        cwd=project_dir,
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.returncode != 0:
        print(f"渲染失败: {result.stderr}")
        return False
    
    return True


def create_remotion_project(script, screenshots_dir):
    project_dir = Path('./tmp/remotion-project')
    project_dir.mkdir(parents=True, exist_ok=True)
    
    create_package_json(project_dir)
    create_tsconfig(project_dir)
    create_src_directory(project_dir, script, screenshots_dir)
    
    public_dir = project_dir / 'public' / 'screenshots'
    public_dir.mkdir(parents=True, exist_ok=True)
    
    if os.path.exists(screenshots_dir):
        for f in os.listdir(screenshots_dir):
            src = os.path.join(screenshots_dir, f)
            dst = public_dir / f
            if os.path.isfile(src):
                shutil.copy2(src, dst)
    
    return project_dir


def create_package_json(project_dir):
    package_json = {
        'name': 'meeting-summary-video',
        'version': '1.0.0',
        'private': True,
        'dependencies': {
            'remotion': '^4.0.0',
            '@remotion/cli': '^4.0.0',
            'react': '^18.0.0',
            'react-dom': '^18.0.0'
        },
        'devDependencies': {
            '@types/react': '^18.0.0',
            'typescript': '^5.0.0'
        },
        'scripts': {
            'build': 'remotion render src/index.tsx MeetingSummary output.mp4'
        }
    }
    
    with open(project_dir / 'package.json', 'w') as f:
        json.dump(package_json, f, indent=2)


def create_tsconfig(project_dir):
    tsconfig = {
        'compilerOptions': {
            'target': 'ES2020',
            'module': 'commonjs',
            'jsx': 'react-jsx',
            'strict': True,
            'esModuleInterop': True,
            'skipLibCheck': True,
            'forceConsistentCasingInFileNames': True,
            'outDir': './dist'
        },
        'include': ['src/**/*']
    }
    
    with open(project_dir / 'tsconfig.json', 'w') as f:
        json.dump(tsconfig, f, indent=2)


def create_src_directory(project_dir, script, screenshots_dir):
    src_dir = project_dir / 'src'
    src_dir.mkdir(exist_ok=True)
    
    with open(src_dir / 'index.tsx', 'w') as f:
        f.write("""import { registerRoot } from 'remotion';
import { RemotionRoot } from './Root';

registerRoot(RemotionRoot);
""")
    
    duration_frames = script['metadata']['duration_seconds'] * 30
    
    with open(src_dir / 'Root.tsx', 'w') as f:
        f.write(f"""import {{ Composition }} from 'remotion';
import {{ MeetingSummary }} from './compositions/MeetingSummary';
import script from './data/script.json';

export const RemotionRoot: React.FC = () => {{
  return (
    <Composition
      id="MeetingSummary"
      component={{MeetingSummary}}
      durationInFrames={duration_frames}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        script: script
      }}
    />
  );
}};
""")
    
    compositions_dir = src_dir / 'compositions'
    compositions_dir.mkdir(exist_ok=True)
    
    with open(compositions_dir / 'MeetingSummary.tsx', 'w') as f:
        f.write(create_meeting_summary_component(script))
    
    data_dir = src_dir / 'data'
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / 'script.json', 'w', encoding='utf-8') as f:
        json.dump(script, f, ensure_ascii=False, indent=2)


def create_meeting_summary_component(script):
    scenes = script.get('scenes', [])
    
    scene_components = []
    current_frame = 0
    
    for scene in scenes:
        duration_frames = scene['duration'] * 30
        
        if scene['type'] == 'title':
            scene_components.append(f"""
      <Sequence from={current_frame} durationInFrames={duration_frames}>
        <TitleScene title="{scene.get('title', '')}" subtitle="{scene.get('subtitle', '')}" />
      </Sequence>""")
        
        elif scene['type'] == 'content':
            bullets = json.dumps(scene.get('bullet_points', []), ensure_ascii=False)
            scene_components.append(f"""
      <Sequence from={current_frame} durationInFrames={duration_frames}>
        <ContentScene content="{scene.get('content', '')}" bulletPoints={{{bullets}}} />
      </Sequence>""")
        
        elif scene['type'] == 'screenshot':
            screenshot_path = scene.get('screenshot', {}).get('path', '')
            if screenshot_path:
                filename = os.path.basename(screenshot_path)
                scene_components.append(f"""
      <Sequence from={current_frame} durationInFrames={duration_frames}>
        <ScreenshotScene imagePath="screenshots/{filename}" caption="{scene.get('screenshot', {}).get('caption', '')}" />
      </Sequence>""")
        
        elif scene['type'] == 'speaker':
            scene_components.append(f"""
      <Sequence from={current_frame} durationInFrames={duration_frames}>
        <SpeakerScene speaker="{scene.get('speaker', '')}" content="{scene.get('content', '')}" />
      </Sequence>""")
        
        elif scene['type'] == 'ending':
            scene_components.append(f"""
      <Sequence from={current_frame} durationInFrames={duration_frames}>
        <EndingScene content="{scene.get('content', '')}" />
      </Sequence>""")
        
        current_frame += duration_frames
    
    return f"""import React from 'react';
import {{ Sequence, useCurrentFrame, useVideoConfig, interpolate, spring }} from 'remotion';
import {{ Img, staticFile }} from 'remotion';

interface MeetingSummaryProps {{
  script: any;
}}

export const MeetingSummary: React.FC<MeetingSummaryProps> = ({{ script }}) => {{
  return (
    <div style={{{{ width: '100%', height: '100%', backgroundColor: '#1a1a1a' }}}}>
      {''.join(scene_components)}
    </div>
  );
}};

const TitleScene: React.FC<{{ title: string; subtitle: string }}> = ({{ title, subtitle }}) => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1]);
  const scale = interpolate(frame, [0, 15], [0.8, 1]);
  
  return (
    <div style={{{{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      opacity,
      transform: `scale(${{scale}})`
    }}}}>
      <h1 style={{{{ fontSize: 72, color: 'white', marginBottom: 20 }}}}>{{title}}</h1>
      <p style={{{{ fontSize: 36, color: 'rgba(255,255,255,0.8)' }}}}>{{subtitle}}</p>
    </div>
  );
}};

const ContentScene: React.FC<{{ content: string; bulletPoints: string[] }}> = ({{ content, bulletPoints }}) => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();
  
  const charsPerSecond = 15;
  const charsToShow = Math.floor((frame / fps) * charsPerSecond);
  const displayedText = content.slice(0, charsToShow);
  
  return (
    <div style={{{{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      justifyContent: 'center',
      padding: 80,
      backgroundColor: '#1a1a1a'
    }}}}>
      <p style={{{{ fontSize: 48, color: 'white', marginBottom: 40 }}}}>{{displayedText}}<span style={{{{ opacity: frame % 30 < 15 ? 1 : 0 }}}}>|</span></p>
      <ul>
        {{bulletPoints.map((point, i) => (
          <li key={{i}} style={{{{ fontSize: 32, color: '#4CAF50', marginBottom: 16 }}}}>{{point}}</li>
        ))}}
      </ul>
    </div>
  );
}};

const ScreenshotScene: React.FC<{{ imagePath: string; caption: string }}> = ({{ imagePath, caption }}) => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1]);
  
  return (
    <div style={{{{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#1a1a1a',
      opacity
    }}}}>
      <Img src={{staticFile(imagePath)}} style={{{{ maxWidth: '90%', maxHeight: '80%' }}}} />
      <p style={{{{ fontSize: 24, color: 'rgba(255,255,255,0.7)', marginTop: 20 }}}}>{{caption}}</p>
    </div>
  );
}};

const SpeakerScene: React.FC<{{ speaker: string; content: string }}> = ({{ speaker, content }}) => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1]);
  
  return (
    <div style={{{{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center',
      backgroundColor: '#1a1a1a',
      opacity
    }}}}>
      <div style={{{{ 
        width: 120, 
        height: 120, 
        borderRadius: '50%', 
        backgroundColor: '#667eea',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 48,
        color: 'white',
        marginBottom: 30
      }}}}>
        {{speaker[0]}}
      </div>
      <p style={{{{ fontSize: 28, color: 'rgba(255,255,255,0.6)', marginBottom: 20 }}}}>{{speaker}}</p>
      <p style={{{{ fontSize: 36, color: 'white', maxWidth: '80%', textAlign: 'center' }}}}>{{content}}</p>
    </div>
  );
}};

const EndingScene: React.FC<{{ content: string }}> = ({{ content }}) => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1]);
  
  return (
    <div style={{{{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      opacity
    }}}}>
      <p style={{{{ fontSize: 48, color: 'white' }}}}>{{content}}</p>
    </div>
  );
}};
"""
