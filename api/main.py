"""
AgentCheck Main Application
FastAPI server and CLI entry points.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import json

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.models.schemas import (
    VerificationRequest,
    VerificationResponse,
    TaskStatus,
    ComplianceReport
)
from api.agents.orchestrator import AgentOrchestrator, create_orchestrator
from api.services.task_queue import TaskQueue


# Initialize FastAPI app
app = FastAPI(
    title="AgentCheck API",
    description="AI-powered certificate verification system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
orchestrator: Optional[AgentOrchestrator] = None
task_queue: Optional[TaskQueue] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get or create orchestrator instance."""
    global orchestrator
    if orchestrator is None:
        orchestrator = create_orchestrator()
    return orchestrator


def get_task_queue() -> TaskQueue:
    """Get or create task queue instance."""
    global task_queue
    if task_queue is None:
        task_queue = TaskQueue()
    return task_queue


@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    global orchestrator, task_queue
    orchestrator = create_orchestrator()
    task_queue = TaskQueue()
    
    # Register task handler
    def handle_verification(task):
        return orchestrator.verify_certificate(
            pdf_path=task.pdf_path,
            simulation_scenario="verified"
        )
    
    task_queue.register_handler(handle_verification)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "AgentCheck",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    orch = get_orchestrator()
    return {
        "status": "healthy",
        "llm_available": orch.llm_client.is_available(),
        "data_dir": str(orch.data_dir),
        "config_dir": str(orch.config_dir)
    }


@app.post("/verify", response_model=VerificationResponse)
async def verify_certificate(
    request: VerificationRequest,
    background_tasks: BackgroundTasks,
    use_function_calling: bool = Query(
        default=True,
        description="Use AI-driven function calling for dynamic tool selection and interpretation"
    )
):
    """
    Verify a certificate PDF.
    
    Args:
        request: Verification request with PDF path or base64 content
        use_function_calling: Enable dynamic tool selection via OpenAI Function Calling
        
    Returns:
        Verification response with task ID and report
    """
    # Create orchestrator with appropriate agent type
    orch = AgentOrchestrator(use_function_calling=use_function_calling)
    
    if not request.pdf_path:
        raise HTTPException(
            status_code=400,
            detail="PDF path is required"
        )
    
    try:
        # Run verification synchronously for simplicity
        report = orch.verify_certificate(
            pdf_path=request.pdf_path,
            simulation_scenario=request.simulation_scenario or "verified"
        )
        
        return VerificationResponse(
            task_id=report.id,
            status=TaskStatus.COMPLETED,
            message="Verification completed successfully",
            report=report
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify/async")
async def verify_certificate_async(
    pdf_path: str,
    scenario: str = "verified"
):
    """
    Queue a certificate verification task.
    
    Returns task ID for status polling.
    """
    queue = get_task_queue()
    task = queue.enqueue(pdf_path)
    
    return {
        "task_id": task.id,
        "status": task.status.value,
        "message": "Task queued for processing"
    }


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a verification task."""
    queue = get_task_queue()
    task = queue.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = {
        "task_id": task.id,
        "status": task.status.value,
        "created_at": task.created_at.isoformat(),
    }
    
    if task.report_id:
        response["report_id"] = task.report_id
    
    if task.error_message:
        response["error"] = task.error_message
    
    return response


@app.get("/reports")
async def list_reports(limit: int = 50):
    """List recent compliance reports."""
    orch = get_orchestrator()
    reports = orch.list_reports(limit)
    return {"reports": reports}


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get a specific compliance report."""
    orch = get_orchestrator()
    report = orch.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report.model_dump(mode='json')


@app.get("/reports/{report_id}/text", response_class=PlainTextResponse)
async def get_report_text(report_id: str):
    """Get report as human-readable text."""
    orch = get_orchestrator()
    report = orch.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return orch.export_report_text(report)


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for verification.
    
    The file is saved to the data/uploads directory.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )
    
    # Save uploaded file
    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "filename": file.filename,
        "path": str(file_path),
        "message": "File uploaded successfully"
    }


# ==================== CLI Interface ====================

def run_cli():
    """Command-line interface for AgentCheck."""
    parser = argparse.ArgumentParser(
        description="AgentCheck - AI Certificate Verification"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify a certificate")
    verify_parser.add_argument("pdf_path", help="Path to the PDF certificate")
    verify_parser.add_argument(
        "--scenario", "-s",
        choices=["verified", "not_verified", "inconclusive", "suspicious", "ambiguous"],
        default="verified",
        help="Simulation scenario for university reply"
    )
    verify_parser.add_argument(
        "--output", "-o",
        help="Output file for report (JSON)"
    )
    verify_parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Output as human-readable text"
    )
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.add_argument(
        "--host",
        default=os.getenv("API_HOST", "0.0.0.0"),
        help="Host to bind to"
    )
    server_parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.getenv("API_PORT", "8000")),
        help="Port to listen on"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List reports")
    list_parser.add_argument(
        "--limit", "-n",
        type=int,
        default=10,
        help="Number of reports to show"
    )
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Get a report")
    report_parser.add_argument("report_id", help="Report ID")
    report_parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Output as human-readable text"
    )
    
    args = parser.parse_args()
    
    if args.command == "verify":
        run_verify(args)
    elif args.command == "server":
        run_server(args)
    elif args.command == "list":
        run_list(args)
    elif args.command == "report":
        run_report(args)
    else:
        parser.print_help()


def run_verify(args):
    """Run verification from CLI."""
    print(f"🔍 Verifying certificate: {args.pdf_path}")
    print(f"📧 Simulation scenario: {args.scenario}")
    print("-" * 50)
    
    orch = create_orchestrator()
    
    try:
        report = orch.verify_certificate(
            pdf_path=args.pdf_path,
            simulation_scenario=args.scenario
        )
        
        print(f"\n✅ Verification complete!")
        print(f"📋 Report ID: {report.id}")
        print(f"🎯 Compliance Result: {report.compliance_result.value}")
        print(f"📊 Verification Status: {report.verification_status.value}")
        print(f"⏱️  Processing Time: {report.processing_time_seconds:.2f}s")
        
        if args.text:
            print("\n" + "=" * 50)
            print(orch.export_report_text(report))
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report.model_dump(mode='json'), f, indent=2, default=str)
            print(f"\n💾 Report saved to: {args.output}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def run_server(args):
    """Start the API server."""
    print(f"🚀 Starting AgentCheck API server...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"📚 Docs: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=False
    )


def run_list(args):
    """List reports from CLI."""
    orch = create_orchestrator()
    reports = orch.list_reports(args.limit)
    
    print(f"📋 Recent Reports ({len(reports)} shown)")
    print("-" * 70)
    
    for r in reports:
        print(f"  {r['id'][:8]}... | {r['compliance_result']:15} | {r['pdf_filename']}")


def run_report(args):
    """Get a specific report from CLI."""
    orch = create_orchestrator()
    report = orch.get_report(args.report_id)
    
    if not report:
        print(f"❌ Report not found: {args.report_id}")
        sys.exit(1)
    
    if args.text:
        print(orch.export_report_text(report))
    else:
        print(json.dumps(report.model_dump(mode='json'), indent=2, default=str))


if __name__ == "__main__":
    run_cli()
