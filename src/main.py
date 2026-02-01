"""Main entry point for GoUP lead generation system."""

import argparse
import sys

from loguru import logger

from .pipeline import LeadGenerationPipeline


def setup_logging(verbose: bool = False):
    """Configure logging."""
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=level,
        colorize=True,
    )
    logger.add(
        "logs/goup_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
    )


def main():
    """Main entry point."""
    # Parent parser for common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser = argparse.ArgumentParser(
        description="GoUP - Lead Generation System for GoHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parent_parser],
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Pilot command
    pilot_parser = subparsers.add_parser(
        "pilot",
        help="Run pilot phase with sample URLs",
        parents=[parent_parser],
    )
    pilot_parser.add_argument(
        "--export",
        action="store_true",
        help="Export results to Google Sheets",
    )

    # Verify command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify if URLs are Shopify stores",
        parents=[parent_parser],
    )
    verify_parser.add_argument(
        "urls",
        nargs="+",
        help="URLs to verify",
    )

    # Process command
    process_parser = subparsers.add_parser(
        "process",
        help="Process specific URLs through the pipeline",
        parents=[parent_parser],
    )
    process_parser.add_argument(
        "urls",
        nargs="+",
        help="URLs to process",
    )
    process_parser.add_argument(
        "--export",
        action="store_true",
        help="Export results to Google Sheets",
    )
    process_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of already-cached domains",
    )

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for Shopify stores and process them",
        parents=[parent_parser],
    )
    search_parser.add_argument(
        "--segment",
        choices=["eyewear", "epharmacy"],
        default="eyewear",
        help="Segment to search for",
    )
    search_parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum number of stores to find",
    )
    search_parser.add_argument(
        "--export",
        action="store_true",
        help="Export results to Google Sheets",
    )
    search_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing of already-cached domains",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging(args.verbose)

    pipeline = LeadGenerationPipeline()

    try:
        if args.command == "pilot":
            leads = pipeline.run_pilot()
            if args.export and leads:
                pipeline.export_to_sheets(leads)

        elif args.command == "verify":
            from .collectors import ShopifyVerifier
            with ShopifyVerifier() as verifier:
                results = verifier.verify_batch(args.urls)
                for result in results:
                    status = "✓ Shopify" if result["is_shopify"] else "✗ Not Shopify"
                    logger.info(f"{result['store_url']}: {status}")

        elif args.command == "process":
            leads = pipeline.process_urls(args.urls, force=args.force)
            pipeline.save_to_json(leads)
            if args.export and leads:
                qualified = [l for l in leads if l.qualification.qualified]
                pipeline.export_to_sheets(qualified)

        elif args.command == "search":
            leads = pipeline.search_and_process(
                segment=args.segment,
                max_results=args.max_results,
                force=args.force,
            )
            pipeline.save_to_json(leads)
            if args.export and leads:
                qualified = [l for l in leads if l.qualification.qualified]
                pipeline.export_to_sheets(qualified)

    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
