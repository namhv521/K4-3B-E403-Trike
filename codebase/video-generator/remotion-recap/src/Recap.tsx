import {AbsoluteFill, Audio, Series, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import type {RecapProps} from "./types";

const Subtitle = ({text, frames}: {text: string; frames: number}) => {
  const frame = useCurrentFrame();
  const words = text.trim().split(/\s+/).filter(Boolean);
  const chunks = words.reduce<string[]>((all, word, index) => {
    const group = Math.floor(index / 6); all[group] = `${all[group] ? `${all[group]} ` : ""}${word}`; return all;
  }, []);
  const current = chunks[Math.min(chunks.length - 1, Math.floor(frame / Math.max(1, frames / Math.max(1, chunks.length))))] || "";
  return <div style={{bottom: 54, left: 80, position: "absolute", right: 80, textAlign: "center"}}><span style={{background: "rgba(4,20,26,.9)", borderRadius: 14, color: "#f7f3eb", display: "inline-block", fontSize: 31, fontWeight: 700, padding: "14px 24px"}}>{current}</span></div>;
};

export const Recap = ({lesson, narrationPath}: RecapProps) => {
  const frame = useCurrentFrame(); const {fps, durationInFrames} = useVideoConfig();
  const fade = interpolate(frame, [0, 12, durationInFrames - 16, durationInFrames], [0, 1, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <AbsoluteFill style={{background: "#081d25", color: "#f7f3eb", fontFamily: "Arial, sans-serif", opacity: fade}}>
    {narrationPath ? <Audio src={staticFile(narrationPath)} /> : null}
    <Series>{lesson.scenes.map((scene, index) => {
      const frames = Math.max(1, Math.round((scene.end - scene.start) * fps));
      return <Series.Sequence key={`${scene.start}-${scene.title}`} durationInFrames={frames}><AbsoluteFill style={{justifyContent: "center", padding: 96}}>
        <div style={{color: "#50d3bc", fontSize: 22, fontWeight: 700}}>VLearn · Ý {index + 1}/{lesson.scenes.length}</div>
        <h1 style={{fontSize: 64, lineHeight: 1.1, margin: "22px 0"}}>{scene.title}</h1><p style={{color: "#c7d8dc", fontSize: 35, lineHeight: 1.4, maxWidth: 940}}>{scene.body}</p><Subtitle text={`${scene.title}. ${scene.body}`} frames={frames} />
      </AbsoluteFill></Series.Sequence>;
    })}</Series>
  </AbsoluteFill>;
};
