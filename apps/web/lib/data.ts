export type Workspace = "engineering" | "forex";
export type Agent = { id: string; name: string; role: string; description: string; workspace: Workspace; accent: string };
export const agents: Agent[] = [
  {id:"alex",name:"Alex",role:"Supervisor",description:"Coordinates tasks and delegates work",workspace:"engineering",accent:"#79cbb0"},
  {id:"sarah",name:"Sarah",role:"Architect",description:"Designs systems and technical boundaries",workspace:"engineering",accent:"#9aa9ff"},
  {id:"prisha",name:"Prisha",role:"UI/UX Designer",description:"Designs interfaces and interaction flows",workspace:"engineering",accent:"#e7a9e5"},
  {id:"james",name:"James",role:"Developer",description:"Implements code and fixes",workspace:"engineering",accent:"#83b8f9"},
  {id:"daniel",name:"Daniel",role:"QA Engineer",description:"Verifies tests and execution evidence",workspace:"engineering",accent:"#f4ca8d"},
  {id:"grace",name:"Grace",role:"Security",description:"Reviews isolation and security risks",workspace:"engineering",accent:"#f3a4a4"},
  {id:"oliver",name:"Oliver",role:"Reviewer",description:"Reviews changes and delivery gates",workspace:"engineering",accent:"#b7b4fd"},
  {id:"market",name:"Maya",role:"Market Analyst",description:"Studies currency pairs and price action",workspace:"forex",accent:"#79cbb0"},
  {id:"macro",name:"Noah",role:"Macro Analyst",description:"Reviews economic events and monetary policy",workspace:"forex",accent:"#9aa9ff"},
  {id:"strategy",name:"Ava",role:"Strategy Research",description:"Designs and evaluates trading hypotheses",workspace:"forex",accent:"#e7a9e5"},
  {id:"risk",name:"Leo",role:"Risk Manager",description:"Reviews exposure and drawdown constraints",workspace:"forex",accent:"#f4ca8d"},
  {id:"execution",name:"Iris",role:"Paper Execution",description:"Simulated orders only; no broker access",workspace:"forex",accent:"#83b8f9"},
  {id:"trade-review",name:"Ethan",role:"Trading Reviewer",description:"Audits research and paper-trade evidence",workspace:"forex",accent:"#b7b4fd"}
];
export type DraftTask = { id: string; workspace: Workspace; text: string; createdAt: string; status: "draft" };
