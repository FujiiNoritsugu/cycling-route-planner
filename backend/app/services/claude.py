"""Claude API service for route analysis and recommendations.

This module handles streaming interactions with the Anthropic Claude API
to provide intelligent route analysis, recommendations, and warnings.
"""

import os
from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic
from anthropic.types import TextDelta

from ..schemas import RouteSegment, WeatherForecast

# Model configuration
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


class ClaudeService:
    """Service for interacting with Claude API for route analysis."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize Claude service.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.

        Raises:
            ValueError: If API key is not provided or found in environment.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in environment or pass to constructor."
            )
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def analyze_route_streaming(
        self,
        segments: list[RouteSegment],
        weather_forecasts: list[WeatherForecast],
        total_distance_km: float,
        total_elevation_gain_m: float,
        difficulty: str,
    ) -> AsyncIterator[str]:
        """Stream route analysis and recommendations from Claude.

        Args:
            segments: Route segments with coordinates and elevation data.
            weather_forecasts: Weather forecasts along the route.
            total_distance_km: Total route distance in kilometers.
            total_elevation_gain_m: Total elevation gain in meters.
            difficulty: Requested difficulty level (easy/moderate/hard).

        Yields:
            Text chunks from Claude's streaming response.
        """
        system_prompt = self._build_system_prompt(
            segments=segments,
            weather_forecasts=weather_forecasts,
            total_distance_km=total_distance_km,
            total_elevation_gain_m=total_elevation_gain_m,
            difficulty=difficulty,
        )

        user_message = (
            "このサイクリングルートを総合的に分析し、"
            "サイクリストにとって有益なアドバイスを日本語で提供してください。"
        )

        async with self.client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for event in stream:
                # Extract text from content block delta events
                if hasattr(event, "type") and event.type == "content_block_delta":
                    if hasattr(event, "delta"):
                        delta = event.delta
                        if isinstance(delta, TextDelta) and hasattr(delta, "text"):
                            yield delta.text

    def _build_system_prompt(
        self,
        segments: list[RouteSegment],
        weather_forecasts: list[WeatherForecast],
        total_distance_km: float,
        total_elevation_gain_m: float,
        difficulty: str,
    ) -> str:
        """Build system prompt with route and weather context.

        Args:
            segments: Route segments.
            weather_forecasts: Weather forecasts.
            total_distance_km: Total distance.
            total_elevation_gain_m: Total elevation gain.
            difficulty: Difficulty level.

        Returns:
            Formatted system prompt for Claude.
        """
        # Weather summary
        weather_summary = self._summarize_weather(weather_forecasts)

        # Route details
        surface_types = [seg.surface_type for seg in segments]
        surface_summary = ", ".join(set(surface_types))

        # Average wind analysis
        avg_wind_speed = (
            sum(w.wind_speed for w in weather_forecasts) / len(weather_forecasts)
            if weather_forecasts
            else 0
        )
        avg_wind_direction = (
            sum(w.wind_direction for w in weather_forecasts) / len(weather_forecasts)
            if weather_forecasts
            else 0
        )

        prompt = f"""あなたは経験豊富なサイクリングルートアドバイザーです。
以下の情報を総合的に分析し、サイクリストに役立つアドバイスを提供してください。

## ルート情報
- 総距離: {total_distance_km:.1f}km
- 獲得標高: {total_elevation_gain_m:.0f}m
- 希望難易度: {difficulty}
- 路面タイプ: {surface_summary}
- セグメント数: {len(segments)}

## 天気情報
{weather_summary}

## 風の状況
- 平均風速: {avg_wind_speed:.1f}m/s
- 平均風向: {avg_wind_direction:.0f}度

## 提供すべき情報（日本語で）
1. **ルートの難易度評価**: 距離、獲得標高、路面タイプから総合評価
2. **補給ポイント推奨**: 距離と標高から休憩・補給が必要な地点を提案
3. **危険箇所の警告**: 強風区間、急勾配、悪天候のタイミングなど
4. **推奨装備**: 天気・気温・風に応じたウェア、補給食、工具など
5. **走行時のアドバイス**: ペース配分、風向きとルート方向の関係、時間帯別注意点

注意点:
- 具体的で実用的なアドバイスを提供してください
- 安全性を最優先してください
- 日本のサイクリング文化に即した表現を使ってください
"""
        return prompt

    def _summarize_weather(self, forecasts: list[WeatherForecast]) -> str:
        """Summarize weather forecasts into human-readable text.

        Args:
            forecasts: List of weather forecasts.

        Returns:
            Weather summary string.
        """
        if not forecasts:
            return "天気情報なし"

        lines = []
        for i, forecast in enumerate(forecasts):
            time_str = forecast.time.strftime("%H:%M")
            temp = forecast.temperature
            wind = forecast.wind_speed
            precip = forecast.precipitation_probability
            desc = forecast.description

            lines.append(
                f"- {time_str}: {desc}, {temp:.1f}°C, "
                f"風速{wind:.1f}m/s, 降水確率{precip:.0f}%"
            )

            # Limit to first 5 forecasts in summary
            if i >= 4:
                if len(forecasts) > 5:
                    lines.append(f"- ...他{len(forecasts) - 5}件")
                break

        return "\n".join(lines)


async def get_claude_service() -> ClaudeService:
    """Dependency injection for ClaudeService.

    Returns:
        Configured ClaudeService instance.
    """
    return ClaudeService()
