from . import types
from .grvt_api_base import GrvtApiConfig, GrvtApiSyncBase, GrvtError


class GrvtApiSync(GrvtApiSyncBase):
    def __init__(self, config: GrvtApiConfig):
        super().__init__(config)
        self.md_rpc = self.env.market_data.rpc_endpoint
        self.td_rpc = self.env.trade_data.rpc_endpoint

    def get_instrument_v1(
        self, req: types.ApiGetInstrumentRequest
    ) -> types.ApiGetInstrumentResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/instrument", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiGetInstrumentResponse(**resp)

    def get_all_instruments_v1(
        self, req: types.ApiGetAllInstrumentsRequest
    ) -> types.ApiGetAllInstrumentsResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/all_instruments", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiGetAllInstrumentsResponse(**resp)

    def get_filtered_instruments_v1(
        self, req: types.ApiGetFilteredInstrumentsRequest
    ) -> types.ApiGetFilteredInstrumentsResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/instruments", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiGetFilteredInstrumentsResponse(**resp)

    def mini_ticker_v1(
        self, req: types.ApiMiniTickerRequest
    ) -> types.ApiMiniTickerResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/mini", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiMiniTickerResponse(**resp)

    def ticker_v1(
        self, req: types.ApiTickerRequest
    ) -> types.ApiTickerResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/ticker", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiTickerResponse(**resp)

    def orderbook_levels_v1(
        self, req: types.ApiOrderbookLevelsRequest
    ) -> types.ApiOrderbookLevelsResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/book", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiOrderbookLevelsResponse(**resp)

    def public_trades_v1(
        self, req: types.ApiPublicTradesRequest
    ) -> types.ApiPublicTradesResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/trades", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiPublicTradesResponse(**resp)

    def public_trade_history_v1(
        self, req: types.ApiPublicTradeHistoryRequest
    ) -> types.ApiPublicTradeHistoryResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/trade_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiPublicTradeHistoryResponse(**resp)

    def candlestick_v1(
        self, req: types.ApiCandlestickRequest
    ) -> types.ApiCandlestickResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/kline", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiCandlestickResponse(**resp)

    def funding_rate_v1(
        self, req: types.ApiFundingRateRequest
    ) -> types.ApiFundingRateResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/funding", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiFundingRateResponse(**resp)

    def settlement_price_v1(
        self, req: types.ApiSettlementPriceRequest
    ) -> types.ApiSettlementPriceResponse | GrvtError:
        resp = self._post(False, self.md_rpc + "/full/v1/settlement", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiSettlementPriceResponse(**resp)

    def create_order_v1(
        self, req: types.ApiCreateOrderRequest
    ) -> types.ApiCreateOrderResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/create_order", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiCreateOrderResponse(**resp)

    def cancel_order_v1(
        self, req: types.ApiCancelOrderRequest
    ) -> types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/cancel_order", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.AckResponse(**resp)

    def cancel_all_orders_v1(
        self, req: types.ApiCancelAllOrdersRequest
    ) -> types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/cancel_all_orders", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.AckResponse(**resp)

    def get_order_v1(
        self, req: types.ApiGetOrderRequest
    ) -> types.ApiGetOrderResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/order", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiGetOrderResponse(**resp)

    def open_orders_v1(
        self, req: types.ApiOpenOrdersRequest
    ) -> types.ApiOpenOrdersResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/open_orders", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiOpenOrdersResponse(**resp)

    def order_history_v1(
        self, req: types.ApiOrderHistoryRequest
    ) -> types.ApiOrderHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/order_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiOrderHistoryResponse(**resp)

    def private_trade_history_v1(
        self, req: types.ApiPrivateTradeHistoryRequest
    ) -> types.ApiPrivateTradeHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/trade_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiPrivateTradeHistoryResponse(**resp)

    def positions_v1(
        self, req: types.ApiPositionsRequest
    ) -> types.ApiPositionsResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/positions", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiPositionsResponse(**resp)

    def deposit_v1(self, req: types.ApiDepositRequest) -> types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/deposit", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.AckResponse(**resp)

    def deposit_history_v1(
        self, req: types.ApiDepositHistoryRequest
    ) -> types.ApiDepositHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/deposit_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiDepositHistoryResponse(**resp)

    def transfer_v1(self, req: types.ApiTransferRequest) -> types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/transfer", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.AckResponse(**resp)

    def transfer_history_v1(
        self, req: types.ApiTransferHistoryRequest
    ) -> types.ApiTransferHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/transfer_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiTransferHistoryResponse(**resp)

    def withdrawal_v1(
        self, req: types.ApiWithdrawalRequest
    ) -> types.AckResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/withdrawal", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.AckResponse(**resp)

    def withdrawal_history_v1(
        self, req: types.ApiWithdrawalHistoryRequest
    ) -> types.ApiWithdrawalHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/withdrawal_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiWithdrawalHistoryResponse(**resp)

    def sub_account_summary_v1(
        self, req: types.ApiSubAccountSummaryRequest
    ) -> types.ApiSubAccountSummaryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/account_summary", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiSubAccountSummaryResponse(**resp)

    def sub_account_history_v1(
        self, req: types.ApiSubAccountHistoryRequest
    ) -> types.ApiSubAccountHistoryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/account_history", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiSubAccountHistoryResponse(**resp)

    def aggregated_account_summary_v1(
        self, req: types.EmptyRequest
    ) -> types.ApiAggregatedAccountSummaryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/aggregated_account_summary", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiAggregatedAccountSummaryResponse(**resp)

    def funding_account_summary_v1(
        self, req: types.EmptyRequest
    ) -> types.ApiFundingAccountSummaryResponse | GrvtError:
        resp = self._post(True, self.td_rpc + "/full/v1/funding_account_summary", req)
        if resp.get("code"):
            return GrvtError(**resp)
        return types.ApiFundingAccountSummaryResponse(**resp)
