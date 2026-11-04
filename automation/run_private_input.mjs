// Keep one stdin-only JSON envelope out of terminal echo and process arguments.
import { spawnSync } from "node:child_process";
if(process.argv.length<3)throw new Error("Command required");
if(process.stdin.isTTY)process.stdin.setRawMode(true);
process.stdin.setEncoding("utf8");
let input="";
process.stdout.write("Ready for private JSON on stdin (input hidden).\n");
process.stdin.on("data",chunk=>{
  if(chunk.includes("\u0003")){process.exit(130);}
  input+=chunk;
  if(input.length>100000)process.exit(64);
  if(!input.includes("\n")&&!input.includes("\r"))return;
  process.stdin.pause();
  const line=input.split(/[\r\n]/)[0];
  const result=spawnSync(process.argv[2],process.argv.slice(3),{input:line+"\n",encoding:"utf8",stdio:["pipe","inherit","inherit"]});
  process.exit(result.status??1);
});
