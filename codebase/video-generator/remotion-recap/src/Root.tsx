import {Composition} from "remotion";
import {Recap} from "./Recap";
import {recapPropsSchema} from "./types";

export const RemotionRoot = () => (
  <Composition id="VLearnRecap" component={Recap} fps={30} width={1280} height={720}
    durationInFrames={2700} schema={recapPropsSchema}
    calculateMetadata={({props}) => ({durationInFrames: Math.max(1, Math.round(props.lesson.duration_seconds * 30))})}
    defaultProps={{lesson: {title: "VLearn recap", duration_seconds: 90, scenes: [{start: 0, end: 90, title: "Đang tải", body: ""}]}, narrationPath: null}} />
);
