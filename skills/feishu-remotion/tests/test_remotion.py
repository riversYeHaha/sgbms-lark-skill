#!/usr/bin/env python3
"""feishu-remotion 单元测试

运行方式:
    cd skills/feishu-remotion
    python -m unittest tests.test_remotion -v
    或
    python tests/test_remotion.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from get_meeting_info import extract_meeting_id, get_meeting_by_link
from get_meeting_minutes import get_meeting_minutes
from generate_script import create_default_script, generate_script, get_llm_client, LLM_PROVIDERS
from capture_screenshots import capture_screenshots, download_meeting_video
from render_video import create_remotion_project, _ts_escape


class TestGetMeetingInfo(unittest.TestCase):
    """测试 get_meeting_info.py"""

    def test_extract_meeting_id_j_pattern(self):
        self.assertEqual(extract_meeting_id('https://vc.feishu.cn/j/123456789'), '123456789')

    def test_extract_meeting_id_s_pattern(self):
        self.assertEqual(extract_meeting_id('https://vc.feishu.cn/s/987654321'), '987654321')

    def test_extract_meeting_id_meeting_id_param(self):
        self.assertEqual(extract_meeting_id('https://vc.feishu.cn/join?meeting_id=555666777'), '555666777')

    def test_extract_meeting_id_trailing_number(self):
        self.assertEqual(extract_meeting_id('https://vc.feishu.cn/123456789'), '123456789')

    def test_extract_meeting_id_fallback(self):
        self.assertEqual(extract_meeting_id('plain-id-123'), 'plain-id-123')

    @patch('get_meeting_info.subprocess.run')
    def test_get_meeting_by_link_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps({
            'topic': '产品周会',
            'start_time': '2026-01-15T10:00:00+08:00',
            'end_time': '2026-01-15T11:00:00+08:00',
            'organizer': '张三',
            'participants': ['李四', '王五'],
            'has_recording': True,
            'has_minutes': True
        }))
        result = get_meeting_by_link('https://vc.feishu.cn/j/123456789')
        self.assertEqual(result['meeting_id'], '123456789')
        self.assertEqual(result['topic'], '产品周会')
        self.assertTrue(result['has_recording'])

    @patch('get_meeting_info.subprocess.run')
    def test_get_meeting_by_link_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='error')
        result = get_meeting_by_link('https://vc.feishu.cn/j/123456789')
        self.assertEqual(result['meeting_id'], '123456789')
        self.assertEqual(result['topic'], '未知会议')
        self.assertFalse(result['has_recording'])


class TestGetMeetingMinutes(unittest.TestCase):
    """测试 get_meeting_minutes.py"""

    @patch('get_meeting_minutes.subprocess.run')
    def test_get_meeting_minutes_success(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps({'items': [{'minutes_id': 'min_456'}]})),
            MagicMock(returncode=0, stdout=json.dumps({
                'transcript': [
                    {'speaker': '张三', 'start_time': '00:00:15', 'end_time': '00:00:45', 'text': '大家好'},
                    {'speaker': '李四', 'start_time': '00:00:46', 'end_time': '00:01:20', 'text': '我认为...'}
                ],
                'summary': '会议讨论了Q1规划',
                'video_url': 'https://example.com/video.mp4'
            }))
        ]
        result = get_meeting_minutes('123456789')
        self.assertIsNotNone(result)
        self.assertEqual(result['meeting_id'], '123456789')
        self.assertEqual(result['minutes_id'], 'min_456')
        self.assertEqual(len(result['transcript']), 2)
        self.assertEqual(result['transcript'][0]['speaker'], '张三')

    @patch('get_meeting_minutes.subprocess.run')
    def test_get_meeting_minutes_search_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr='error')
        result = get_meeting_minutes('123456789')
        self.assertIsNone(result)

    @patch('get_meeting_minutes.subprocess.run')
    def test_get_meeting_minutes_no_items(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps({'items': []}))
        result = get_meeting_minutes('123456789')
        self.assertIsNone(result)


class TestGenerateScript(unittest.TestCase):
    """测试 generate_script.py"""

    def test_llm_providers_config(self):
        self.assertIn('deepseek', LLM_PROVIDERS)
        self.assertIn('kimi', LLM_PROVIDERS)
        self.assertIn('glm', LLM_PROVIDERS)
        self.assertIn('volcengine', LLM_PROVIDERS)
        self.assertEqual(LLM_PROVIDERS['deepseek']['base_url'], 'https://api.deepseek.com/v1')

    def test_get_llm_client_missing_provider(self):
        with self.assertRaises(ValueError) as ctx:
            get_llm_client('nonexistent')
        self.assertIn('不支持的 LLM 提供商', str(ctx.exception))

    def test_get_llm_client_missing_api_key(self):
        env_key = LLM_PROVIDERS['deepseek']['env_key']
        if env_key in os.environ:
            del os.environ[env_key]
        with self.assertRaises(ValueError) as ctx:
            get_llm_client('deepseek')
        self.assertIn('未设置', str(ctx.exception))

    def test_create_default_script_structure(self):
        transcript = {'summary': '测试会议', 'transcript': []}
        script = create_default_script(transcript, 'summary', 180)
        self.assertEqual(script['version'], '1.0')
        self.assertIn('metadata', script)
        self.assertIn('scenes', script)
        self.assertEqual(script['metadata']['style'], 'summary')
        self.assertEqual(len(script['scenes']), 3)
        self.assertEqual(script['scenes'][0]['type'], 'title')
        self.assertEqual(script['scenes'][1]['type'], 'content')
        self.assertEqual(script['scenes'][2]['type'], 'ending')

    def test_create_default_script_title_truncation(self):
        long_title = '这是一个非常长的会议标题超过二十个字符'
        transcript = {'summary': long_title, 'transcript': []}
        script = create_default_script(transcript, 'summary', 180)
        self.assertLessEqual(len(script['metadata']['title']), 20)

    @patch('generate_script.get_llm_client')
    def test_generate_script_with_mock_llm(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
            'version': '1.0',
            'metadata': {'title': '测试', 'duration_seconds': 30, 'style': 'summary', 'total_scenes': 2},
            'scenes': [
                {'scene_id': 1, 'type': 'title', 'title': '测试', 'duration': 3},
                {'scene_id': 2, 'type': 'ending', 'content': '结束', 'duration': 3}
            ]
        })))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = (mock_client, 'deepseek-chat')

        transcript = {
            'summary': '测试会议',
            'transcript': [
                {'speaker': '张三', 'text': '大家好'},
                {'speaker': '李四', 'text': '今天讨论...'}
            ]
        }
        script = generate_script(transcript, 'summary', 180, 'deepseek')
        self.assertEqual(script['metadata']['title'], '测试')
        self.assertEqual(len(script['scenes']), 2)

    @patch('generate_script.get_llm_client')
    def test_generate_script_llm_returns_invalid_json(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='不是 JSON'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = (mock_client, 'deepseek-chat')

        transcript = {'summary': '测试', 'transcript': []}
        script = generate_script(transcript, 'summary', 180, 'deepseek')
        # 应该回退到默认脚本
        self.assertEqual(script['metadata']['style'], 'summary')
        self.assertEqual(len(script['scenes']), 3)


class TestCaptureScreenshots(unittest.TestCase):
    """测试 capture_screenshots.py"""

    @patch('capture_screenshots.download_meeting_video')
    @patch('capture_screenshots.subprocess.run')
    def test_capture_screenshots_success(self, mock_run, mock_download):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, 'test.mp4')
            Path(video_path).touch()
            mock_download.return_value = video_path
            mock_run.return_value = MagicMock(returncode=0)

            script = {
                'scenes': [
                    {'scene_id': 1, 'type': 'title', 'duration': 3},
                    {'scene_id': 2, 'type': 'screenshot', 'duration': 5, 'screenshot': {
                        'needed': True, 'timestamp': '00:05:00', 'caption': '架构图'
                    }},
                    {'scene_id': 3, 'type': 'screenshot', 'duration': 5, 'screenshot': {
                        'needed': False, 'timestamp': '00:10:00'
                    }}
                ]
            }
            output_dir = os.path.join(tmpdir, 'screenshots')
            result = capture_screenshots('123', script, output_dir)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['scene_id'], 2)
            self.assertEqual(result[0]['timestamp'], '00:05:00')
            # subprocess is mocked so file won't exist; verify path format instead
            self.assertTrue(result[0]['path'].endswith('screenshot_002.jpg'))

    @patch('capture_screenshots.download_meeting_video')
    def test_capture_screenshots_no_video(self, mock_download):
        mock_download.return_value = None
        script = {'scenes': [{'type': 'screenshot', 'screenshot': {'needed': True}}]}
        result = capture_screenshots('123', script, '/tmp/test')
        self.assertEqual(result, [])

    @patch('capture_screenshots.shutil.which')
    @patch('capture_screenshots.subprocess.run')
    def test_download_meeting_video_already_exists(self, mock_run, mock_which):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / 'meeting_123.mp4'
            video_path.touch()
            result = download_meeting_video('123', tmpdir)
            self.assertEqual(result, str(video_path))
            mock_run.assert_not_called()

    @patch('capture_screenshots.shutil.which')
    def test_download_meeting_video_no_ffmpeg(self, mock_which):
        mock_which.return_value = None
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_meeting_video('123', tmpdir)
            self.assertIsNone(result)


class TestRenderVideo(unittest.TestCase):
    """测试 render_video.py"""

    def test_ts_escape_basic(self):
        self.assertEqual(_ts_escape('hello'), 'hello')

    def test_ts_escape_backslash(self):
        self.assertEqual(_ts_escape('a\\b'), 'a\\\\b')

    def test_ts_escape_double_quote(self):
        self.assertEqual(_ts_escape('say "hi"'), 'say \\"hi\\"')

    def test_ts_escape_newline(self):
        self.assertEqual(_ts_escape('line1\nline2'), 'line1 line2')

    def test_create_remotion_project_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script = {
                'metadata': {'duration_seconds': 30},
                'scenes': [
                    {'type': 'title', 'title': '测试', 'subtitle': '副标题', 'duration': 3},
                    {'type': 'content', 'content': '要点', 'bullet_points': ['A', 'B'], 'duration': 5},
                    {'type': 'screenshot', 'duration': 4, 'screenshot': {'needed': True, 'path': '/tmp/test.jpg', 'caption': '图'}},
                    {'type': 'speaker', 'speaker': '张三', 'content': '发言', 'duration': 3},
                    {'type': 'ending', 'content': '谢谢', 'duration': 2}
                ]
            }
            screenshots_dir = os.path.join(tmpdir, 'screenshots')
            os.makedirs(screenshots_dir)
            Path(screenshots_dir, 'test.jpg').touch()

            project_dir = create_remotion_project(script, screenshots_dir, tmpdir)

            # 验证文件结构
            self.assertTrue(os.path.exists(os.path.join(project_dir, 'package.json')))
            self.assertTrue(os.path.exists(os.path.join(project_dir, 'tsconfig.json')))
            self.assertTrue(os.path.exists(os.path.join(project_dir, 'src', 'index.tsx')))
            self.assertTrue(os.path.exists(os.path.join(project_dir, 'src', 'Root.tsx')))
            self.assertTrue(os.path.exists(os.path.join(project_dir, 'src', 'data', 'script.json')))

            # 验证组件文件
            scenes_dir = os.path.join(project_dir, 'src', 'compositions', 'scenes')
            self.assertTrue(os.path.exists(os.path.join(scenes_dir, 'TitleScene.tsx')))
            self.assertTrue(os.path.exists(os.path.join(scenes_dir, 'ContentScene.tsx')))
            self.assertTrue(os.path.exists(os.path.join(scenes_dir, 'ScreenshotScene.tsx')))
            self.assertTrue(os.path.exists(os.path.join(scenes_dir, 'SpeakerScene.tsx')))
            self.assertTrue(os.path.exists(os.path.join(scenes_dir, 'EndingScene.tsx')))

            # 验证共享组件
            components_dir = os.path.join(project_dir, 'src', 'components')
            self.assertTrue(os.path.exists(os.path.join(components_dir, 'Typewriter.tsx')))
            self.assertTrue(os.path.exists(os.path.join(components_dir, 'FadeIn.tsx')))

            # 验证 MeetingSummary.tsx 包含所有场景
            meeting_summary_path = os.path.join(project_dir, 'src', 'compositions', 'MeetingSummary.tsx')
            with open(meeting_summary_path, 'r') as f:
                content = f.read()
            self.assertIn('TitleScene', content)
            self.assertIn('ContentScene', content)
            self.assertIn('ScreenshotScene', content)
            self.assertIn('SpeakerScene', content)
            self.assertIn('EndingScene', content)

            # 验证截图被复制到 public
            self.assertTrue(os.path.exists(os.path.join(project_dir, 'public', 'screenshots', 'test.jpg')))

    def test_create_remotion_project_empty_script(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script = {'metadata': {'duration_seconds': 10}, 'scenes': []}
            project_dir = create_remotion_project(script, '/nonexistent', tmpdir)
            self.assertTrue(os.path.exists(os.path.join(project_dir, 'src', 'compositions', 'MeetingSummary.tsx')))


class TestIntegration(unittest.TestCase):
    """集成测试 — 验证脚本间的协作"""

    def test_script_pipeline_with_mock_data(self):
        """模拟完整流程的数据流转"""
        meeting_info = {
            'meeting_id': '123456789',
            'topic': '产品周会',
            'has_recording': True,
            'has_minutes': True
        }
        minutes = {
            'meeting_id': '123456789',
            'transcript': [
                {'speaker': '张三', 'text': '今天讨论Q1规划'},
                {'speaker': '李四', 'text': '移动端优化优先'}
            ],
            'summary': 'Q1产品规划会议'
        }

        # 验证 generate_script 能处理 minutes 格式
        with patch('generate_script.get_llm_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
                'version': '1.0',
                'metadata': {'title': '产品周会', 'duration_seconds': 60, 'style': 'summary', 'total_scenes': 3},
                'scenes': [
                    {'scene_id': 1, 'type': 'title', 'title': '产品周会', 'duration': 3},
                    {'scene_id': 2, 'type': 'content', 'content': 'Q1规划', 'bullet_points': ['移动端'], 'duration': 10},
                    {'scene_id': 3, 'type': 'ending', 'content': '谢谢', 'duration': 2}
                ]
            })))]
            mock_client.chat.completions.create.return_value = mock_response
            mock_get_client.return_value = (mock_client, 'deepseek-chat')

            script = generate_script(minutes, 'summary', 180, 'deepseek')
            self.assertEqual(script['metadata']['title'], '产品周会')
            self.assertEqual(len(script['scenes']), 3)

            # 验证 render_video 能处理生成的脚本
            with tempfile.TemporaryDirectory() as tmpdir:
                project_dir = create_remotion_project(script, '/nonexistent', tmpdir)
                self.assertTrue(os.path.exists(os.path.join(project_dir, 'src', 'data', 'script.json')))
                with open(os.path.join(project_dir, 'src', 'data', 'script.json'), 'r') as f:
                    saved_script = json.load(f)
                self.assertEqual(saved_script['metadata']['title'], '产品周会')


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_extract_meeting_id_empty_string(self):
        self.assertEqual(extract_meeting_id(''), '')

    def test_extract_meeting_id_only_slashes(self):
        self.assertEqual(extract_meeting_id('///'), '')

    def test_create_default_script_empty_transcript(self):
        script = create_default_script({'summary': '', 'transcript': []}, 'quick', 30)
        self.assertEqual(script['metadata']['title'], '会议总结')
        self.assertEqual(script['metadata']['style'], 'quick')

    def test_capture_screenshots_no_screenshot_scenes(self):
        script = {'scenes': [{'type': 'title'}, {'type': 'ending'}]}
        result = capture_screenshots('123', script, '/tmp/test')
        self.assertEqual(result, [])

    def test_capture_screenshots_no_needed_flag(self):
        script = {'scenes': [{'type': 'screenshot', 'screenshot': {'needed': False}}]}
        result = capture_screenshots('123', script, '/tmp/test')
        self.assertEqual(result, [])

    def test_render_video_ts_escape_special_chars(self):
        self.assertEqual(_ts_escape('\\"\n'), '\\\\\\" ')


if __name__ == '__main__':
    unittest.main(verbosity=2)
