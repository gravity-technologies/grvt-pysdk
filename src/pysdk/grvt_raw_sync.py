from enum import Enum

from dacite import Config, from_dict

from . import grvt_raw_types
from .grvt_raw_base import GrvtApiConfig, GrvtError, GrvtRawSyncBase

# mypy: disable-error-code="no-any-return"


class GrvtRawSync(GrvtRawSyncBase):
    def __init__(self, config: GrvtApiConfig):
        super().__init__(config)
        self.md_rpc = self.env.market_data.rpc_endpoint
        self.td_rpc = self.env.trade_data.rpc_endpoint

    def get_instrument_v1(
        self, req: grvt_raw_types.ApiGetInstrumentRequest
    ) -> grvt_raw_types.ApiGetInstrumentResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/instrument", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiGetInstrumentResponse, resp, Config(cast=[Enum])
        )

    def get_all_instruments_v1(
        self, req: grvt_raw_types.ApiGetAllInstrumentsRequest
    ) -> grvt_raw_types.ApiGetAllInstrumentsResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/all_instruments", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiGetAllInstrumentsResponse, resp, Config(cast=[Enum])
        )

    def get_filtered_instruments_v1(
        self, req: grvt_raw_types.ApiGetFilteredInstrumentsRequest
    ) -> grvt_raw_types.ApiGetFilteredInstrumentsResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/instruments", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiGetFilteredInstrumentsResponse, resp, Config(cast=[Enum])
        )

    def mini_ticker_v1(
        self, req: grvt_raw_types.ApiMiniTickerRequest
    ) -> grvt_raw_types.ApiMiniTickerResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/mini", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiMiniTickerResponse, resp, Config(cast=[Enum]))

    def ticker_v1(
        self, req: grvt_raw_types.ApiTickerRequest
    ) -> grvt_raw_types.ApiTickerResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/ticker", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiTickerResponse, resp, Config(cast=[Enum]))

    def orderbook_levels_v1(
        self, req: grvt_raw_types.ApiOrderbookLevelsRequest
    ) -> grvt_raw_types.ApiOrderbookLevelsResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/book", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiOrderbookLevelsResponse, resp, Config(cast=[Enum])
        )

    def trade_v1(
        self, req: grvt_raw_types.ApiTradeRequest
    ) -> grvt_raw_types.ApiTradeResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/trade", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiTradeResponse, resp, Config(cast=[Enum]))

    def trade_history_v1(
        self, req: grvt_raw_types.ApiTradeHistoryRequest
    ) -> grvt_raw_types.ApiTradeHistoryResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/trade_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiTradeHistoryResponse, resp, Config(cast=[Enum])
        )

    def candlestick_v1(
        self, req: grvt_raw_types.ApiCandlestickRequest
    ) -> grvt_raw_types.ApiCandlestickResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/kline", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiCandlestickResponse, resp, Config(cast=[Enum]))

    def funding_rate_v1(
        self, req: grvt_raw_types.ApiFundingRateRequest
    ) -> grvt_raw_types.ApiFundingRateResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/funding", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiFundingRateResponse, resp, Config(cast=[Enum]))

    def create_order_v1(
        self, req: grvt_raw_types.ApiCreateOrderRequest
    ) -> grvt_raw_types.ApiCreateOrderResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/create_order", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiCreateOrderResponse, resp, Config(cast=[Enum]))

    def cancel_order_v1(
        self, req: grvt_raw_types.ApiCancelOrderRequest
    ) -> grvt_raw_types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/cancel_order", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.AckResponse, resp, Config(cast=[Enum]))

    def cancel_all_orders_v1(
        self, req: grvt_raw_types.ApiCancelAllOrdersRequest
    ) -> grvt_raw_types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/cancel_all_orders", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.AckResponse, resp, Config(cast=[Enum]))

    def get_order_v1(
        self, req: grvt_raw_types.ApiGetOrderRequest
    ) -> grvt_raw_types.ApiGetOrderResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/order", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiGetOrderResponse, resp, Config(cast=[Enum]))

    def open_orders_v1(
        self, req: grvt_raw_types.ApiOpenOrdersRequest
    ) -> grvt_raw_types.ApiOpenOrdersResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/open_orders", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiOpenOrdersResponse, resp, Config(cast=[Enum]))

    def order_history_v1(
        self, req: grvt_raw_types.ApiOrderHistoryRequest
    ) -> grvt_raw_types.ApiOrderHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/order_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiOrderHistoryResponse, resp, Config(cast=[Enum])
        )

    def fill_history_v1(
        self, req: grvt_raw_types.ApiFillHistoryRequest
    ) -> grvt_raw_types.ApiFillHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/fill_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiFillHistoryResponse, resp, Config(cast=[Enum]))

    def positions_v1(
        self, req: grvt_raw_types.ApiPositionsRequest
    ) -> grvt_raw_types.ApiPositionsResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/positions", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.ApiPositionsResponse, resp, Config(cast=[Enum]))

    def deposit_v1(
        self, req: grvt_raw_types.ApiDepositRequest
    ) -> grvt_raw_types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/deposit", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.AckResponse, resp, Config(cast=[Enum]))

    def deposit_history_v1(
        self, req: grvt_raw_types.ApiDepositHistoryRequest
    ) -> grvt_raw_types.ApiDepositHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/deposit_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiDepositHistoryResponse, resp, Config(cast=[Enum])
        )

    def transfer_v1(
        self, req: grvt_raw_types.ApiTransferRequest
    ) -> grvt_raw_types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/transfer", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.AckResponse, resp, Config(cast=[Enum]))

    def transfer_history_v1(
        self, req: grvt_raw_types.ApiTransferHistoryRequest
    ) -> grvt_raw_types.ApiTransferHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/transfer_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiTransferHistoryResponse, resp, Config(cast=[Enum])
        )

    def withdrawal_v1(
        self, req: grvt_raw_types.ApiWithdrawalRequest
    ) -> grvt_raw_types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/withdrawal", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(grvt_raw_types.AckResponse, resp, Config(cast=[Enum]))

    def withdrawal_history_v1(
        self, req: grvt_raw_types.ApiWithdrawalHistoryRequest
    ) -> grvt_raw_types.ApiWithdrawalHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/withdrawal_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiWithdrawalHistoryResponse, resp, Config(cast=[Enum])
        )

    def sub_account_summary_v1(
        self, req: grvt_raw_types.ApiSubAccountSummaryRequest
    ) -> grvt_raw_types.ApiSubAccountSummaryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/account_summary", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiSubAccountSummaryResponse, resp, Config(cast=[Enum])
        )

    def sub_account_history_v1(
        self, req: grvt_raw_types.ApiSubAccountHistoryRequest
    ) -> grvt_raw_types.ApiSubAccountHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/account_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiSubAccountHistoryResponse, resp, Config(cast=[Enum])
        )

    def aggregated_account_summary_v1(
        self, req: grvt_raw_types.EmptyRequest
    ) -> grvt_raw_types.ApiAggregatedAccountSummaryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/aggregated_account_summary", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiAggregatedAccountSummaryResponse, resp, Config(cast=[Enum])
        )

    def funding_account_summary_v1(
        self, req: grvt_raw_types.EmptyRequest
    ) -> grvt_raw_types.ApiFundingAccountSummaryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/funding_account_summary", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return from_dict(
            grvt_raw_types.ApiFundingAccountSummaryResponse, resp, Config(cast=[Enum])
        )
